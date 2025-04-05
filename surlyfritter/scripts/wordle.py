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

import collections
import getpass
import sys
import statistics

from wordle import BadInput, LocationConstraint, WordleConstraints, WordList, WordleWord

NUM_GUESSES = 6


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
    if verbose:
        print(f"{target}:")
    constraints = WordleConstraints([])
    try:
        for i in range(NUM_GUESSES):
            guess = matching_words(words, constraints, 1)[0]
            new_constraints = get_constraints(target, guess)
            constraints.update_constraints(new_constraints)
            if verbose:
                print(f"\tguess {i+1}: {guess}, {constraints}")
    except WordMatch as match:
        match.guess_count = i + 1
        if verbose:
            print(f"\tguess {match.guess_count}: {guess}")
        raise match
    raise WordMatchFail(f"no match for {target}")


def solve_and_report(words: WordList, is_secret=False) -> None:
    all_words = WordList()
    is_specified_words = len(words.words) != len(all_words.words)

    matches = []
    fails = []
    for i, word in enumerate(words):
        if i % 500 == 0 and not is_specified_words:
            print(f"{i+1} / {len(words.words)}, {word} {len(matches)} {len(fails)}")
        try:
            if word not in all_words:
                raise WordMatchFail("not in Wordle list")
            verbose = is_specified_words and not is_secret
            solve_wordle(target=str(word), words=all_words, verbose=verbose)
        except WordMatch as match:
            matches.append(match)
        except WordMatchFail as fail:
            if is_specified_words:
                fail_word = "secret word" if is_secret else f"'word'"
                print(f"Can't solve {fail_word}: {fail}")
            fail.guess_count = NUM_GUESSES + 1
            fails.append(word)

    if is_secret:
        if matches:
            print(f"Guesses to find word: {matches[0].guess_count}")
        if fails:
            print(f"Couldn't find {[w for w in words]}")

    if not is_specified_words:
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
        counts = collections.Counter(guess_counts)
        for k, v in sorted(counts.items(), key=lambda x: x[0]):
            print(k, v)
        print()
        print("Failed words:")
        print(list(sorted(fails, key=lambda x: x.word)))


def suggest_next_words(num, args_start):
    args = sys.argv[args_start:]
    constraints = WordleConstraints(args)
    words = WordList()
    words = matching_words(words, constraints, num)
    for word in words:
        if word.satisfies_constraints(constraints):
            print(f"{word.score:.3f} {word}")


def matching_words(words: WordList, constraints: WordleConstraints, num=None):
    if constraints:
        words = [w for w in words if w.satisfies_constraints(constraints)]
    words = sorted(words, key=lambda x: x.score)
    if not words:
        raise WordMatchFail(f"no words for constraints {constraints}")
    return words[-num:] if num else words


def main():
    """Supply 'help' for today's wordle puzzle"""
    try:
        # Solve mode: one or more args, and the first arg is either -s or -S.
        #     Just the -s or -S arg:
        #         -s: solve every wordle word and print statistics about it
        #         -S: read a word in without displaying it (password mode) to avoid spoilers
        #     two or more args:
        #         -s: solve the word given as the 2+-th args
        #
        is_solve_all = len(sys.argv) == 2 and sys.argv[1] == "-s"
        is_solve_one = len(sys.argv) > 2 and sys.argv[1] == "-s"
        is_solve_one_secret = len(sys.argv) == 2 and sys.argv[1] == "-S"
        is_solve = is_solve_one or is_solve_one_secret or is_solve_all

        if is_solve:
            if is_solve_one:
                words = WordList(sys.argv[2:])
            elif is_solve_one_secret:
                word = getpass.getpass("Wordle word to solve: ")
                words = WordList([word])
            elif is_solve_all:
                words = WordList()
            else:
                raise BadInput("bad solve args???")
            solve_and_report(words, is_solve_one_secret)

        else:
            if len(sys.argv) > 1 and sys.argv[1] == "-a":
                num = None
                args_start = 2
            else:
                if len(sys.argv) > 1 and sys.argv[1] == "-S":
                    raise BadInput("Error: if used, -S should be the only arg")
                num = 1
                args_start = 1
            suggest_next_words(num, args_start)

    except WordMatchFail as err:
        print(err)
    except BadInput as err:
        print(err)


if __name__ == "__main__":
    main()
