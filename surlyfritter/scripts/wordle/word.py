"""Wordle word classes"""

import os
from collections.abc import Iterator
from collections import Counter
from pathlib import Path

from .constraints import LENGTH, LocationConstraint, WordleConstraints


class BadWordleWord(Exception):
    """Exception for words that are not valid wordle words"""


class WordleWord:
    """
    Class to model a Wordle word
    """

    @property
    def right_length(self):
        return len(self.word) == LENGTH

    @property
    def is_wordle_word(self) -> bool:
        """Is this a valid Wordle word?"""
        return self.right_length and "'" not in self.word

    def __init__(self, word: str) -> None:
        self.word = word.strip().lower()
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

        for constraint in constraints:
            if not self.satisfies_one(constraint):
                return False
        return True

    def satisfies_one(self, constraint: LocationConstraint) -> bool:
        """
        For the given constraint, is this word a possible solution?

        Does the word have the right letters in the right locations, and not
        in the wrong places? The input "constraint" is a LocationConstraint
        object indicating for one letter where it is or is not allowed. E.g.
        in the below, "a" is the third letter, and cannot be in the second or
        fourth position; "b" is in the word but cannot be the fourth letter,
        and "c" is the second letter:

                "a" -> dict(yes=[2], no=[1,3]),
                "b" -> dict(yes=[], no=[3]),
                "c" -> dict(yes=[1], no=[]),

        1) Is the letter in the word?
        2) if the letter's position is known, is the letter in that position?
        3) if there are excluded spots for the letter, is it NOT in the position?
        """
        return (
            constraint.word_has_letter(self.word)
            and constraint.all_yeses(self.word)
            and constraint.no_forbiddens(self.word)
        )

    def __iter__(self) -> Iterator:
        """Iterate over the characters of this word"""
        return self.word.__iter__()


class WordList:
    """A list of the Wordle-valid words in a file"""

    ENVAR = "WORDS"
    FILE = "/usr/share/dict/american-english"

    def __init__(self, envar_name: str = ENVAR) -> None:
        """
        Create a wordlist from the file specified in the environment variable
        """
        self.words = set()

        # Read in words
        word_file = Path(os.environ.get(envar_name, WordList.FILE))
        with word_file.open() as lines:
            for line in lines:
                try:
                    wordle_word = WordleWord(line)
                    self.words.add(wordle_word)
                except BadWordleWord:
                    continue

        # Calculate each word's score, which requires runing make_letter_scores first
        self.make_letter_scores()
        for word in self:
            word.score = self.word_score(word)

    def make_letter_scores(self):
        """Determine how frequent each letter is in this word set"""
        self.letter_scores = {}
        letter_counts = Counter([letter for word in self.words for letter in word])
        for letter, count in letter_counts.items():
            self.letter_scores[letter] = count / letter_counts.total()

        # Normalize
        max_letter_score = max(self.letter_scores.values())
        for letter, count in self.letter_scores.items():
            self.letter_scores[letter] = count / max_letter_score

    def word_score(self, word):
        """
        Assign a score for this word. Higher is better. Favor letter commonness
        (for the set of letters in wordle words) and larger numbers of unique
        letters.
        """
        commonness_score = sum(self.letter_scores[c] for c in word) / LENGTH
        count_score = len(set(word)) / LENGTH
        return (commonness_score + count_score) / 2.0

    def __iter__(self) -> Iterator:
        """Make this class's words attribute the iterable"""
        return self.words.__iter__()
