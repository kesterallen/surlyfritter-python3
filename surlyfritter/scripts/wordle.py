"""
Wordle "assistance" program

Specify letters that are NOT in the wordle by adding them to the BAD_LETTERS
string.  Specify letters that ARE in the wordle by putting their known location
in the LETTERS[letter]["yes"] list, or by putting locations they are not in
into the LETTERS[letter]["no"] list. For example, this will produce "swill":

    BAD_LETTERS = "abcdefghjkmnopqrt"
    LETTERS = dict(
        s=dict(yes=[0], no=[2, 4]),
        l=dict(yes=[3, 4], no=[]),
    )

"""

BAD_LETTERS = "abcdefghjkmnopqrt"
LETTERS = dict(
    s=dict(yes=[0], no=[2, 4]),
    l=dict(yes=[3, 4], no=[]),
)


def get_words(dict_name="/usr/share/dict/american-english"):
    """ Return every 5-character work in a dictionary file. """
    words = []
    with open(dict_name) as lines:
        for line in lines:
            word = line.strip()
            if len(word) == 5 and "'" not in word and word.islower():
                words.append(word)
    return words


def letter_locations_good(word, letters):
    """
    Does the word have the right letters in the right locations, and not in the
    wrong places?
    """
    goods = []
    for letter, locations in letters.items():
        # Is the letter in the word at all?
        goods.append(letter in word)

        # If the letter's position is known, is it in the right place?
        if locations["yes"]:
            for location in locations["yes"]:
                goods.append(word[location] == letter)

        # If there are excluded spots for the letter, is it NOT there in this word?
        if locations["no"]:
            for location in locations["no"]:
                goods.append(word[location] != letter)
    return all(goods)


def main():
    """Get the wordle"""
    for word in get_words():
        no_bad_letters = all((l not in word for l in BAD_LETTERS))
        in_right_places = letter_locations_good(word, LETTERS)

        if no_bad_letters and in_right_places:
            print(word)


if __name__ == "__main__":
    main()
