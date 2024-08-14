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

    goods = []
    for letter, locations in letters.items():
        is_here = letter in word
        in_right_places = all([word[i] == letter for i in locations["yes"]])
        not_in_wrong_places = all([word[i] != letter for i in locations["no"]])

        goods.append(is_here and in_right_places and not_in_wrong_places)

    return all(goods)


class BadInput(Exception):
    pass


def parse_good_letter_yes_no_input(good_letter_input):
    """
    Parse a single good-letter input_gl of the form:
        +12
    or
        -45
    and return data to update good_letters with.
    """
    CHAR_LIMIT = (1, 5)

    # Skip empty inputs, which will occur if only one of + or -,  but not both
    # are specified:
    #
    if good_letter_input is None:
        return

    # The first char should be + or -; if so translate it to yes
    # or no, if not bail out:
    #
    firstchar = good_letter_input[0]
    if firstchar not in ("+", "-"):
        raise BadInput(f"input {good_letter_input} is invalid")
    yesno = "yes" if firstchar == "+" else "no"

    positions = [int(p) for p in good_letter_input[1:]]
    if any([p > CHAR_LIMIT[1] or p < CHAR_LIMIT[0] for p in positions]):
        raise BadInput(f"input {good_letter_input} is invalid")

    # User inputs are 1-based, string indices are 0-based
    return yesno, [p-1 for p in positions]


def parse_good_letter_input(good_letters, cli_input):
    """
    Parse a single good-letter input of the form:
        r+1-34
    (The wordle word has an "r" for the first letter, and the third and fourth letters are NOT "r".)
        b+23
    ("b" is the second and third letter)
        m-1345
    ("m" is a letter, but not the first, third, fourth, or fifth letter in the word)

    and update the good_letters dict in place.

    Note that e.g. "r+1-34" is exactly equivilent to "r-34+1".
    """

    # This regex splits a string of the form "x+123-45" into ("x", "+", "12", "-", "45")
    #
    # GOOD_LETTER_REGEX = r"(\w)([-+]?)(\w*)([-+]?)(\w*)"
    GOOD_LETTER_REGEX = r"(\w)([-+]\w*)?([-+]\w*)?"
    result = re.search(GOOD_LETTER_REGEX, cli_input)
    if result is None:
        raise BadInput(f"good-letter argument {cli_input} isn't valid")

    (letter, limits1, limits2) = result.groups()
    if letter not in good_letters:
        good_letters[letter] = {"yes": [], "no": []}

    for limits in (limits1, limits2):
        if limits is None:
            continue
        yesno, positions = parse_good_letter_yes_no_input(limits)
        print(letter, yesno, positions)
        good_letters[letter][yesno].extend(positions)


def parse_inputs(cli_inputs):
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
    good_letters = {}

    for cli_input in cli_inputs:
        if "+" in cli_input or "-" in cli_input:
            parse_good_letter_input(good_letters, cli_input)
        else:
            # check for bad_letters
            bad_letters += cli_input

    validate_inputs(bad_letters, good_letters)
    print(bad_letters, good_letters)
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
            errors.append(f"LETTERS locations must be a dict, not {locations}")
        if "yes" not in locations:
            errors.append(f"LETTERS locations must have a 'yes' array as a key {locations}")
        if "no" not in locations:
            errors.append(f"LETTERS locations must have a 'no' array as a key {locations}")
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
                pass
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
