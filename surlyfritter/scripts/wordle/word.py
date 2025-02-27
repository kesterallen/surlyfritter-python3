"""Wordle word classes"""

import os
from collections.abc import Iterator
from collections import Counter
from pathlib import Path

from . import BadInput
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
        return self.word.islower() and self.right_length and "'" not in self.word

    def __init__(self, word: str) -> None:
        self.word = word.strip()
        self.letters = set(c for c in self.word)
        if not self.is_wordle_word:
            raise BadWordleWord(f"{word} is not a valid wordle entry")

    def __repr__(self) -> str:
        return self.word

    def contains_bad_letters(self, constraints: WordleConstraints) -> bool:
        """Determine if self.word contains any of the characters in BAD_LETTERS"""
        return constraints.bad_letters.intersection(self.letters)

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
            constraint.word_has_letter(self.letters)
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

    def __init__(self, words_input: [list[str] | str] = ENVAR) -> None:
        """
        Create a wordlist from either a list of words or a file specified via
        environment variable
        """
        self.words = set()

        # Read in words from file or a list of words
        from_filename = isinstance(words_input, str)
        if from_filename:
            word_file = Path(os.environ.get(words_input, WordList.FILE))
            with word_file.open() as lines:
                words = list(lines)
        else:
            words = words_input

        # Convert to WordleWord objects
        for word in words:
            try:
                wordle_word = WordleWord(word)
                self.words.add(wordle_word)
            except BadWordleWord:
                if not from_filename:
                    print(f"{word} is not a valid wordle entry")
                continue

        if len(self.words) == 0:
            raise BadInput(f"No valid wordle words in {words_input}")

        # Calculate each word's score, which requires runing make_letter_scores first
        self.make_letter_scores()
        for word in self:
            word.score = self.word_score(word)

        max_word_score = max(word.score for word in self)
        for word in self:
            word.score /= max_word_score

    def make_letter_scores(self):
        self.letter_scores = {}
        letter_counts = Counter([letter for word in self.words for letter in word])
        for letter, count in letter_counts.items():
            self.letter_scores[letter] = count / letter_counts.total()

    def word_score(self, word):
        """Give this word a frequency score, higher is better"""
        letter_commonness = sum(self.letter_scores[letter] for letter in word)
        letter_count_score = len(set(word)) / 5
        return letter_commonness + letter_count_score

    def __iter__(self) -> Iterator:
        """Make this class's words attribute the iterable"""
        return self.words.__iter__()

    def __contains__(self, word: WordleWord) -> bool:
        """Override the "in" operator"""
        return any(word.word == str(w) for w in self.words)
