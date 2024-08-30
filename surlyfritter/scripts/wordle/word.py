"""Wordle word classes"""

import os
from collections.abc import Iterator
from pathlib import Path

from .constraints import LENGTH, LocationConstraint, WordleConstraints


class BadWordleWord(Exception):
    """Exception for words that are not valid wordle words"""


class WordleWord:
    """
    Class to model a Wordle word
    """

    @property
    def is_wordle_word(self) -> bool:
        """Is this a valid Wordle word?"""
        return self.word.islower() and len(self.word) == LENGTH and "'" not in self.word

    def __init__(self, word: str) -> None:
        self.word = word.strip()
        if not self.is_wordle_word:
            raise BadWordleWord(f"{word} is not a valid wordle entry")

    def __repr__(self) -> str:
        return self.word

    def contains_bad_letters(self, constraints: WordleConstraints) -> bool:
        """Determine if 'word' contains any of the characters in BAD_LETTERS"""
        return any(c in constraints.bad_letters for c in self.word)

    def satisfies_constraints(self, constraints: WordleConstraints) -> bool:
        """
        Check if this word is a valid wordle solution for these constraints
        """
        if self.contains_bad_letters(constraints):
            return False

        # for constraint in constraints:
        #    if not self.satisfies_one(constraint):
        #        return False
        # return True
        return all(self.satisfies_one(c) for c in constraints)

    def satisfies_one(self, constraint: LocationConstraint) -> bool:
        """
        For the given constraint, is this word a possible solution?

        Does the word have the right letters in the right locations, and not in the
        wrong places? The input "constraint" is a LocationConstraint object
        indicating for one letter where it is or is not allowed. E.g. in the below,
        "a" is the third letter, and cannot be in the second or fourth position;
        "b" is in the word but cannot be the fourth letter, and "c" is the second letter:

                "a" -> dict(yes=[2], no=[1,3]),
                "b" -> dict(yes=[], no=[3]),
                "c" -> dict(yes=[1], no=[]),

        1) Is the letter in the word?
        2) if the letter's position is known, is the letter in that position?
        3) if there are excluded spots for the letter, is it NOT in the position?
        """
        return (
            constraint.letter in self.word
            and constraint.all_yeses(self.word)
            and constraint.no_forbiddens(self.word)
        )


class WordList:
    """A list of the Wordle-valid words in a file"""

    ENVAR = "WORDS"
    FILE = "/usr/share/dict/american-english"

    def __init__(self, envar_name: str = ENVAR) -> None:
        """Create a wordlist from the file specified in the environment variable"""
        self.words = set()

        word_file = Path(os.environ.get(envar_name, WordList.FILE))
        with word_file.open() as lines:
            for line in lines:
                try:
                    wordle_word = WordleWord(line)
                    self.words.add(wordle_word)
                except BadWordleWord:
                    continue

    def __iter__(self) -> Iterator:
        """Make this class's words attribute the iterable"""
        return self.words.__iter__()
