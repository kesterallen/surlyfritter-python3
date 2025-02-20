"""Wordle constraints classes"""

import re
from collections.abc import Iterator

LENGTH = 5


class BadInput(Exception):
    """Exception to throw for bad user inputs"""


class LocationConstraint:
    """Class to model the yes/no locations for one letter in the Wordle"""

    YES = "yes"
    NO = "no"
    YESNO = {YES, NO}
    LOCATIONS_REGEX = r"([-+]?\d+)"

    def __init__(self, constraint_input: str) -> None:
        """
        Parse and load a single good-letter input of the form:

            r+1-34
        (The wordle word has an "r" for the first letter, and the third and
        fourth letters are NOT "r".)
        (i.e. a letter, then one or more matches to LOCATIONS_REGEX)

        If specified first, the + can be skipped, i.e. r+1-34 is the same as
        r1-34.

        or:
            b+23
        ("b" is the second and third letter)

        or:
            m-1345
        ("m" is a letter, but not the first, third, fourth, or fifth letter
        in the word)

        and return an update for the location_constraints dict.

        Note that e.g. "r+1-34" is exactly equivalent to "r-34+1",
        """
        if not constraint_input:
            raise BadInput(f"constraint input {constraint_input} isn't truthy")

        letter = constraint_input[0]
        if not letter.isalpha():
            raise BadInput(f"constraint input {constraint_input} is nonalpha")
        self.letter = letter

        # This regex / findall generates lists like:
        #   "+123-45" -> ["+123", "-45"]
        #   or "45-12" -> ["45", "-12"]
        #   or "-14" -> ["-14"]
        #
        locations = re.findall(self.LOCATIONS_REGEX, constraint_input)
        if not locations:
            raise BadInput(f"constraint input {constraint_input} has no matches")

        self.coordinates = {self.YES: [], self.NO: []}
        for location in locations:
            self.update_coordinates(location)

    @property
    def yes(self) -> list[int]:
        """Syntactic sugar for the "yes" coordinate list"""
        return self.coordinates[self.YES]

    @property
    def no(self) -> list[int]:
        """Syntactic sugar for the "no" coordinate list"""
        return self.coordinates[self.NO]

    def update_coordinates(self, location: str) -> None:
        """
        Parse a single good-letter input string of the form:
            +12
            (or 12)
        or
            -45
        and return a dict like {"a": {"yes": [0, 1], "no": [2, 4]}} to update
        location_constraints with.
        """

        if not re.match(self.LOCATIONS_REGEX, location):
            raise BadInput(
                f"Location {location} should match {self.LOCATIONS_REGEX}, doesn't"
            )

        # The first char should be + or -; if so translate it to yes or no, if
        # not bail out. If there are just digits, assume that firstchar is "+":
        #
        firstchar = location[0]

        if firstchar in ("+", "-"):
            yesno = self.YES if firstchar == "+" else self.NO
            digits = location[1:]
        else:
            if not firstchar.isdigit():
                err = f"Input {location} is invalid: no leading +/-, not numbers"
                raise BadInput(err)
            yesno = self.YES
            digits = location

        positions = [int(p) for p in digits]
        if not all(LENGTH >= p >= 1 for p in positions):
            raise BadInput(f"input {location}: numbers must be between 1 and 5")

        # User inputs are 1-based, string indices are 0-based
        positions = [p - 1 for p in positions]
        self.coordinates[yesno].extend(positions)

    def word_has_letter(self, word):
        return self.letter in word

    def all_yeses(self, word: str) -> bool:
        """Does the word match every required position for this constraint?"""
        yeses = {word[i] == self.letter for i in self.yes}
        return all(yeses)

    def no_forbiddens(self, word: str) -> bool:
        """Does the word have none of forbidden positions for this constraint?"""
        forbiddens = {word[i] == self.letter for i in self.no}
        return not any(forbiddens)

    def __str__(self) -> str:
        yes = "".join([str(i+1) for i in self.yes])
        no = "-" + "".join([str(i+1) for i in self.no]) if self.no else ""
        return f"{self.letter}{yes}{no}"

class WordleConstraints:
    """
    Parse inputs of the form:
        BAD_LETTERS goodletter+location-nothere_nothere_nothere
    with 1-based indexes, e.g.
        adusort e-123 i+3 h+5-12

    to produce two instance attributes: a bad_letters string and a
    set of LocationConstraint objects

        self.bad_letters = set("adusort")
        self.location_constraints = [
            location_constraint(e: (yes=[], no=[3])),
            location_constraint(i: (yes=[2], no=[])),
            location_constraint(h: (yes=[4], no=[1, 2])),
        ]
    """

    def __init__(self, input_strs: list[str]) -> None:
        self.bad_letters = set()
        self.location_constraints = {}

        for input_str in input_strs:
            if any(c.isdigit() for c in input_str):
                lc = LocationConstraint(input_str)
                self.update_location_constraints(lc)
            else:
                for letter in input_str:
                    self.bad_letters.add(letter)

        # Check that bad letters aren't in location_constraints
        for lc in self.location_constraints.values():
            if lc.letter in self.bad_letters:
                raise BadInput(f"Letter '{lc.letter}' can't be in both GOOD and BAD")

    def update_location_constraints(self, lc: LocationConstraint):
        if lc.letter in self.location_constraints:
            for yesno in LocationConstraint.YESNO:
                coords = lc.coordinates[yesno]
                self.location_constraints[lc.letter].coordinates[yesno].extend(coords)
        else:
            self.location_constraints[lc.letter] = lc

    def update_constraints(self, other):
        self.bad_letters = self.bad_letters.union(other.bad_letters)
        for lc in other:
            self.update_location_constraints(lc)

    def __str__(self) -> str:
        output = ["".join(sorted(self.bad_letters))]
        for lc in self.location_constraints.values():
            output.append(str(lc) )
        return " ".join(output)

    def __iter__(self) -> Iterator:
        """Make this class's location_constraints attribute the iterable"""
        return self.location_constraints.values().__iter__()
        #return self.location_constraints.__iter__()
