"""
Wordle "assistance" program

Specify inputs for excluded letters and letters that are or are not at a location with this syntax:

        adst e-123 i+3 h+5-12

(The letters a, d, s, and t are excluded, e is present but is NOT the first, second,
or third letter, and h is the fifth letter but not the first or second.)
"""

import re
import sys

DEBUG = False
DEFAULT_WORD_FILE = "/usr/share/dict/american-english"
WORDLE_LENGTH = 5


class BadInput(Exception):
    """Exception to throw for bad user inputs"""


def is_wordle_word(word: str) -> bool:
    """
    Is the input word a valid wordle word?
        * 5 characters
        * no apostrophes
        * all lower-case (to remove proper nouns)
    """
    return word.islower() and len(word.strip()) == WORDLE_LENGTH and "'" not in word


def all_wordle_words(word_file: str = DEFAULT_WORD_FILE) -> set[str]:
    """Return a set of every WORDLE_LENGTH-character word in a word list file."""
    with open(word_file, encoding="utf8") as words:
        return {w.strip() for w in words if is_wordle_word(w)}


def location_ok(word: str, letter_locations: dict) -> bool:
    """
    Does the word have the right letters in the right locations, and not in the
    wrong places? The input "locations" should be a dict with key/value pairs
    indicating which letter should go where, and where each letter is not
    allowed. E.g. in the below, "a" is the third letter, and cannot be in the
    second or fourth position; "b" is in the word but cannot be the fourth
    letter, and "c" is the second letter:

        dict(
            a=dict(yes=[2], no=[1,3]),
            b=dict(yes=[], no=[3]),
            c=dict(yes=[1], no=[]),
        )

    1) Is the letter in the word?
    2) if the letter's position is known, is the letter in that position?
    3) if there are excluded spots for the letter, is it NOT in the position?
    """
    is_location_ok = set()
    for letter, locations in letter_locations.items():
        is_here = letter in word
        all_right_places = all(word[i] == letter for i in locations["yes"])
        no_wrong_places = all(word[i] != letter for i in locations["no"])

        is_location_ok.update((is_here, all_right_places, no_wrong_places))

    return all(is_location_ok)


def parse_location(letter_locs_input: str | None) -> tuple[str, list[int]]:
    """
    Parse a single good-letter input_gl of the form:
        +12
        (or 12)
    or
        -45
    and return data to update letter_locations with.
    """
    # Skip empty inputs, which will occur if only one of + or -,  but not both
    # are specified:
    #
    if letter_locs_input is None:
        raise BadInput("letter_locs_input is 'None'")

    # The first char should be + or -; if so translate it to yes or no, if not
    # bail out. If there are just digits, assume that firstchar should be "+":
    #
    firstchar = letter_locs_input[0]
    if firstchar not in ("+", "-"):
        if firstchar.isdigit():
            yesno = "yes"
            digits = letter_locs_input
        else:
            raise BadInput(f"input {letter_locs_input} is invalid, no leading +/-")
    else:
        yesno = "yes" if firstchar == "+" else "no"
        digits = letter_locs_input[1:]

    positions = [int(p) for p in digits]
    if any(p > WORDLE_LENGTH or p < 1 for p in positions):
        raise BadInput(f"input {letter_locs_input}: numbers must be between 1 and 5")

    # User inputs are 1-based, string indices are 0-based
    return yesno, [p - 1 for p in positions]


def parse_letter_location(_input: str) -> dict:
    """
    Parse a single good-letter _input of the form:

        r+1-34
    (The wordle word has an "r" for the first letter, and the third and fourth
    letters are NOT "r".)

    If specified first, the + can be skipped, i.e. r+1-34 is the same as r1-34.

    or:
        b+23
    ("b" is the second and third letter)

    or:
        m-1345
    ("m" is a letter, but not the first, third, fourth, or fifth letter in the word)

    and return an update for the letter_locations dict.

    Note that e.g. "r+1-34" is exactly equivalent to "r-34+1",
    """
    # This regex splits a string of the form
    #   "x+123-45" into ("x", "+123", "-45")
    #   or "y45-12" into ("y", "+45", "-12")
    #   or "z-14" into ("z", "-14", None)
    #
    letter_locs_regex = r"(\w)([-+]?\d+)([-+]?\d+)?"
    result = re.search(letter_locs_regex, _input)
    if result is None:
        raise BadInput(f"good-letter argument {_input} isn't valid")

    (letter, location1, location2) = result.groups()
    letter_location = {letter: {"yes": [], "no": []}}

    for location in (location1, location2):
        if location is not None:
            yesno, positions = parse_location(location)
            letter_location[letter][yesno].extend(positions)

    return letter_location


def parse_inputs(inputs: list[str]) -> tuple[str, dict]:
    """
    Parse input of the form:
        BAD_LETTERS goodletter+location-nothere_nothere_nothere
    with 1-based indexes, e.g.
        adusort e-123 i+3 h+5-12

    to produce a bad_letters string and a letters dict with this structure:

        BAD_LETTERS = "adusort"
        LETTERS = dict(
            e=dict(yes=[], no=[3]),
            i=dict(yes=[2], no=[]),
            h=dict(yes=[4], no=[1, 2]),
    )
    """
    bad_letters = ""
    letter_locations = {}

    # If there's a number in the input, it's a good letter
    # Otherwise it's a bad letter
    for _input in inputs:
        if any(c.isdigit() for c in _input):
            letter_location = parse_letter_location(_input)
            letter_locations.update(letter_location)
        else:
            bad_letters += _input

    validate_inputs(bad_letters, letter_locations)
    return bad_letters, letter_locations


def validate_inputs(bad_letters: str, letter_locations: dict) -> None:
    """Sanity check user inputs"""

    duplicated_letters = {b for b in bad_letters if b in letter_locations}
    if duplicated_letters:
        raise BadInput(f"Dups {duplicated_letters} in BAD_LETTERS and LETTERS")

    if not isinstance(letter_locations, dict):
        raise BadInput("LETTERS should be a dict")

    errors = []
    for letter, locations in letter_locations.items():
        if len(letter) != 1:
            errors.append("LETTER LOCS can only have single-character keys")
        if not isinstance(locations, dict):
            errors.append(f"LETTER LOCS must be a dict, not {locations}")
        if "yes" not in locations:
            errors.append(f"LETTER LOCS must have a 'yes' array as a key {locations}")
        if "no" not in locations:
            errors.append(f"LETTER LOCS must have a 'no' array as a key {locations}")
    if errors:
        raise BadInput(";".join(errors))


def no_bad_letters(word: str, bad_letters: str) -> bool:
    """Determine if 'word' contains any of the characters in BAD_LETTERS"""
    return not any(bl in word for bl in bad_letters)


def is_possible_word(word: str, bad_letters: str, letter_locations: dict) -> bool:
    """Is the word a possible solution?"""
    return no_bad_letters(word, bad_letters) and location_ok(word, letter_locations)


def main():
    """Get the wordle"""
    try:
        bad_letters, letter_locations = parse_inputs(sys.argv[1:])
        words = []
        for word in all_wordle_words():
            if is_possible_word(word, bad_letters, letter_locations):
                words.append(word)

        print("\n".join(words))

        if DEBUG:
            print("")
            print(f"Count: {len(words)}")
            print(f"Excluded letters: {bad_letters}")
            print(f"Included letters: {letter_locations}")
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
