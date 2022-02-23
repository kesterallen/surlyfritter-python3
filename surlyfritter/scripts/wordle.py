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

BAD_LETTERS = "ishortwrottropkvshoutcpr"
LETTERS = dict(
    a=dict(yes=[], no=[0, 1]),
    d=dict(yes=[], no=[1]),
    e=dict(yes=[], no=[3, 4]),
)

DEFAULT_WORD_FILE = "/usr/share/dict/american-english"


def is_wordle_word(line):
    """
    Does the input line contain a wordle word? (5-char, not a proper noun).
    If so, return it, otherwise return None.
    """
    word = line.strip()
    if len(word) != 5 or "'" in word or not word.islower():
        word = None
    return word


def get_words(word_file=DEFAULT_WORD_FILE):
    """Return every 5-character work in a word list file."""
    with open(word_file, encoding="utf8") as lines:
        words = {is_wordle_word(l) for l in lines}
    words.remove(None)
    return words


def letter_locations_good(word, letters):
    """
    Does the word have the right letters in the right locations, and not in the
    wrong places?
    """
    goods = []
    for letter, locations in letters.items():
        # Is the letter in the word?
        goods.append(letter in word)

        # If the letter's position is known, is the letter in that position?
        if locations["yes"]:
            for location in locations["yes"]:
                goods.append(word[location] == letter)

        # If there are excluded spots for the letter, is it NOT there in this word?
        if locations["no"]:
            for location in locations["no"]:
                goods.append(word[location] != letter)
    return all(goods)


def validate_inputs():
    """Sanity check user inputs"""
    errors = {b for b in BAD_LETTERS if b in LETTERS}
    if errors:
        error = ", ".join(errors)
        print(f"Error: Letter(s) '{error}' are in both LETTERS and BAD_LETTERS")


def main():
    """Get the wordle"""
    validate_inputs()

    for word in get_words():
        no_bad_letters = all((l not in word for l in BAD_LETTERS))
        in_right_places = letter_locations_good(word, LETTERS)

        if no_bad_letters and in_right_places:
            print(word)


if __name__ == "__main__":
    main()
