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

import sys


BAD_LETTERS = "dieshorclpm"
LETTERS = dict(
    a=dict(yes=[], no=[0,2,3]),
    u=dict(yes=[], no=[1,3,4]),
    t=dict(yes=[4], no=[]),
)

DEFAULT_WORD_FILE = "/usr/share/dict/american-english"


def wordle_filter(line):
    """
    Is the input line a wordle word? 
        * 5 characters
        * no apostrophes
        * all lower-case (to remove proper nouns)
    If so return it, otherwise return None.
    """
    word = line.strip()
    if len(word) != 5 or "'" in word or not word.islower():
        word = None
    return word


def get_words(word_file=DEFAULT_WORD_FILE):
    """Return every 5-character work in a word list file."""
    with open(word_file, encoding="utf8") as lines:
        words = {wordle_filter(line) for line in lines}
    words.remove(None)
    return words


def letter_locations_good(word, letters):
    """
    Does the word have the right letters in the right locations, and not in the
    wrong places? The input "letters" should be a dict with keys 

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


def validate_inputs():
    """Sanity check user inputs"""
    error = None

    duped_letters = {b for b in BAD_LETTERS if b in LETTERS}
    if duped_letters:
        dup_str = ", ".join(duped_letters)
        error = f"Letters {dup_str} are in BAD_LETTERS and LETTERS"

    if not isinstance(LETTERS, dict):
        error = "LETTERS should be a dict"

    for letter, locations in LETTERS.items():
        if len(letter) != 1:
            error = "LETTERS can only have single-character keys"
        if not isinstance(locations, dict):
            error = "LETTERS locations must be a dict"
        if "yes" not in locations:
            error = "LETTERS locations must have a yes array as a key"
        if "no" not in locations:
            error = "LETTERS locations must have a no array as a key"

    if error:
        print("Error", error)
        sys.exit(1)

def main():
    """Get the wordle"""
    validate_inputs()

    for word in get_words():
        no_bad_letters = all((bl not in word for bl in BAD_LETTERS))
        in_right_places = letter_locations_good(word, LETTERS)

        if no_bad_letters and in_right_places:
            print(word)


if __name__ == "__main__":
    main()
