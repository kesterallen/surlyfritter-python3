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
import statistics

from wordle import BadInput, LocationConstraint, WordleConstraints, WordList, WordleWord


class WordMatch(Exception):
    pass


class WordMatchFail(Exception):
    pass


def get_constraints(word: str, guess: WordleWord) -> WordleConstraints:
    if word == str(guess):
        raise WordMatch(f"word match: {word}!!")

    constraints = WordleConstraints([])
    for i, letter in enumerate(guess):
        if letter not in word:
            constraints.bad_letters.add(letter)
        else:
            prefix = "+" if letter == word[i] else "-"
            lc = LocationConstraint(f"{letter}{prefix}{i+1}")
            constraints.update_location_constraints(lc)
    return constraints


def solve_wordle(target: str, words: WordList, verbose: bool):
    constraints = WordleConstraints([])
    try:
        for i in range(6):
            guess = matching_words(words, constraints, 1)
            new_constraints = get_constraints(target, guess[0])
            constraints.update_constraints(new_constraints)
            if verbose:
                print(f"guess {i+1}: {guess[0]}, {constraints}")
    except WordMatch as match:
        match.guess_count = i + 1
        if verbose:
            print(f"guess {match.guess_count}: {guess[0]}")
        raise match
    raise WordMatchFail(f"no match for {target}")


def matching_words(words: WordList, constraints: WordleConstraints, num=None):
    if constraints:
        words = [w for w in words if w.satisfies_constraints(constraints)]
    words = sorted(words, key=lambda x: x.score)
    return words[-num:] if num else words


def main():
    """Supply 'help' for today's wordle puzzle"""
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "-s":
            SOLVER = True
            words = WordList(sys.argv[2], read_from_file=False) if len(sys.argv) > 2 else WordList()
            only_one_word = len(words.words) == 1
            matches = []
            fails = []
            for i, word in enumerate(words):
                if i % 500 == 0 and not only_one_word:
                    print(f"{i} / {len(words.words)}, {word} {len(matches)} {len(fails)}")
                try:
                    solve_wordle(target=str(word), words=WordList(), verbose=only_one_word)
                except WordMatch as match:
                    matches.append(match)
                except WordMatchFail:
                    fails.append(word)

            if not only_one_word:
                success_rate = (len(matches) + 1) / (len(words.words) + 1)
                guess_counts = [match.guess_count for match in matches]
                guess_mean = statistics.mean(guess_counts)
                guess_median = statistics.median(guess_counts)
                guess_stdev = statistics.stdev(guess_counts)
                guess_min = min(guess_counts)
                guess_max = max(guess_counts)
                print(
                    f"success rate: {success_rate:.2f}, "
                    f"guess_mean {guess_mean:.2f} +/- {guess_stdev:.2f}, guess_median {guess_median:.2f} "
                    f"min={guess_min}, max={guess_max}"
                )
                print()
                print("Failed words:")
                print(fails)
        else:
            SOLVER = False
            constraints = WordleConstraints(sys.argv[1:])
            words = WordList()
            words = matching_words(words, constraints, 1)
            for word in words:
                if word.satisfies_constraints(constraints):
                    print(f"{word.score:.3f} {word}")
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
