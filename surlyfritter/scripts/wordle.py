"""
Wordle "assistance" program

Specify letters that are NOT in the wordle by adding them to the BAD_LETTERS
string.

Specify letters that ARE in the wordle by putting their known location in the
LETTERS[letter]["yes"] list, or by putting locations they are not in into the
LETTERS[letter]["no"] list. For example, this will produce "swill":

    BAD_LETTERS = "abcdefghjkmnopqrt"
    LETTERS = dict(
        s=dict(yes=[0], no=[2, 4]),
        l=dict(yes=[3, 4], no=[]),
    )

"""

import re
import sys

# BAD_LETTERS = "adusort"
# LETTERS = dict(
#    # a=dict(yes=[], no=[0, 1, 2]),
#    e=dict(yes=[], no=[3]),
#    i=dict(yes=[2], no=[]),
#    h=dict(yes=[], no=[1]),
# )

DEFAULT_WORD_FILE = "/usr/share/dict/american-english"


def is_wordle_word(word: str) -> bool:
    """
    Is the input word a valid wordle word?
        * 5 characters
        * no apostrophes
        * all lower-case (to remove proper nouns)
    """
    return word.islower() and len(word.strip()) == 5 and "'" not in word


def get_wordle_words(word_file: str = DEFAULT_WORD_FILE) -> set[str]:
    """Return a set of every 5-character word in a word list file."""
    with open(word_file, encoding="utf8") as words:
        return {w.strip() for w in words if is_wordle_word(w)}


def is_possible_word(word: str, letters: dict) -> bool:
    """
    Does the word have the right letters in the right locations, and not in the
    wrong places? The input "letters" should be a dict with key/value pairs
    indicating which letter should go where, and where each letter is not
    allowed. E.g. in the below, "a" is the third letter, and cannot be in the
    second or fourth position; "b" is in the word but cannot be the fourth
    letter, and "c" is the second letter:

        dict(
            a=dict(yes=[2], no=[1,3]),
            b=dict(yes=[], no=[3]),
            c=dict(yes=[1], no=[]),
        )

    1) Is the letter in the word? 2) if the letter's position(s) is
    known, is the letter in that position? 3) if there are excluded spots
    for the letter, is it NOT in the location?
    """

    # TODO: validate word
    # TODO: validate letters

    goods = []
    for letter, locations in letters.items():
        is_here = letter in word
        in_right_places = all([word[i] == letter for i in locations["yes"]])
        not_in_wrong_places = all([word[i] != letter for i in locations["no"]])

        goods.append(is_here and in_right_places and not_in_wrong_places)

    return all(goods)


class BadInput(Exception):
    pass


def parse_inputs(inputs):
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
    # badlettters g+1-2

    GOOD_LETTER_REGEX = r"(\w)([-+]?)(\w*)([-+]?)(\w*)"
    GOOD_LETTER_DIRECTIONS = {"+": "yes", "-": "no", "": "yes"}

    bad_letters = ""
    good_letters = {}

    for input in inputs:
        if "+" in input or "-" in input:
            result = re.search(GOOD_LETTER_REGEX, input)
            if result is None:
                raise BadInput(f"good-letter argument {input} isn't valid")
            (letter, dir1, pos1, dir2, pos2) = result.groups()

            for dir, pos_str in ((dir1, pos1), (dir2, pos2)):
                name = GOOD_LETTER_DIRECTIONS[dir]
                if name:
                    if letter not in good_letters:
                        good_letters[letter] = {"yes": [], "no": []}
                    for p in pos_str:
                        try:
                            pos = int(p)
                            if pos > 5 or pos < 1:
                                raise BadInput(f"pos is {pos}, should be 1, 2, 3, 4, or 5")
                            pos_0based = pos - 1
                            # TODO check pos between 1 and 5, inclusive
                        except ValueError:
                            continue
                        good_letters[letter][name].append(pos_0based)
        else:
            # check for bad_letters
            bad_letters += input

    validate_inputs(bad_letters, good_letters)
    return bad_letters, good_letters


def validate_inputs(bad_letters, letters):
    """Sanity check user inputs"""

    duplicated_letters = {b for b in bad_letters if b in letters}
    if duplicated_letters:
        raise BadInput(f"Dups {duplicated_letters} in BAD_LETTERS and LETTERS")

    if not isinstance(letters, dict):
        raise BadInput("LETTERS should be a dict")

    errors = []
    for letter, locations in letters.items():
        if len(letter) != 1:
            errors.append("LETTERS can only have single-character keys")
        if not isinstance(locations, dict):
            errors.append("LETTERS locations must be a dict, not {locations}")
        if "yes" not in locations:
            errors.append("LETTERS locations must have a 'yes' array as a key")
        if "no" not in locations:
            errors.append("LETTERS locations must have a 'no' array as a key")
    if errors:
        raise BadInput(";".join(errors))


def no_bad_letters(word, bad_letters):
    """Determine if 'word' contains any of the characters in BAD_LETTERS"""
    return not any(bl in word for bl in bad_letters)


def main():
    """Get the wordle"""
    try:
        bad_letters, letters = parse_inputs(sys.argv[1:])
        for word in get_wordle_words():
            if no_bad_letters(word, bad_letters) and is_possible_word(word, letters):
                print(word)
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
