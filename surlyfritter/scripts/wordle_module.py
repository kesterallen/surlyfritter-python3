"""
Wordle "assistance" program

Specify inputs for excluded letters and letters that are or are not at a
location with this syntax:

        adst e-123 i+3 h+5-12

    or (pluses are optional):
        adst e-123 i3 h5-12

(The letters a, d, s, and t are excluded, e is present but is NOT the first,
second, or third letter, i is the third letter, and h is the fifth letter but
not the first or second.)
"""

import sys
from wordle.constraints import BadInput, WordleConstraints
from wordle.word import WordList


def main():
    """Supply 'help' for today's wordle puzzle"""
    try:
        constraints = WordleConstraints(sys.argv[1:])
        for word in WordList():
            if word.satisfies_constraints(constraints):
                print(word)
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
