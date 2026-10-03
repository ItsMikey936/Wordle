"""The scoring rules.

:func:`evaluate` is a pure function of two words: same inputs, same marks, no
side effects and no knowledge of the board. That makes the only genuinely
tricky part of Wordle — repeated letters — cheap to test in isolation.
"""

from __future__ import annotations

from collections import Counter

from .domain import STATUS_PRIORITY, LetterResult, LetterStatus
from .words import normalize


def evaluate(guess: str, secret: str) -> tuple[LetterResult, ...]:
    """Mark every letter of ``guess`` against ``secret``.

    Both words are normalised first, so ``"  PÉRRRO "`` and ``"perro"`` are
    the same guess and ``ñ`` survives as a letter of its own.

    Two passes, because order decides the answer when letters repeat:

    1. Greys everything, then promotes every letter sitting in its own spot to
       green and spends one of that letter's copies.
    2. Walks the guess left to right and promotes the remaining greys to
       yellow, but only while that letter still has an unspent copy left.

    Spending greens first is what makes ``LLAMA`` against ``SILLA`` come out
    ``PRESENT, PRESENT, ABSENT, ABSENT, CORRECT``: the green ``A`` used up the
    secret's only ``A``, so the ``A`` further left cannot be yellow.
    """
    guess = normalize(guess)
    secret = normalize(secret)

    if len(guess) != len(secret):
        raise ValueError(
            f"cannot compare a {len(guess)}-letter guess "
            f"with a {len(secret)}-letter secret"
        )

    results = [LetterResult(letter, LetterStatus.ABSENT) for letter in guess]
    unspent = Counter(secret)

    for index, letter in enumerate(guess):
        if letter == secret[index] and unspent[letter] > 0:
            results[index] = LetterResult(letter, LetterStatus.CORRECT)
            unspent[letter] -= 1

    for index, letter in enumerate(guess):
        if results[index].status is LetterStatus.ABSENT and unspent[letter] > 0:
            results[index] = LetterResult(letter, LetterStatus.PRESENT)
            unspent[letter] -= 1

    return tuple(results)


def merge(current: LetterStatus, incoming: LetterStatus) -> LetterStatus:
    """Combine two marks of the same letter, keeping the best one.

    This is what stops the on-screen keyboard from showing a letter as grey
    again after a later guess proved it green.
    """
    if STATUS_PRIORITY[incoming] > STATUS_PRIORITY[current]:
        return incoming
    return current


def merge_results(
    previous: tuple[LetterStatus, ...],
    incoming: tuple[LetterStatus, ...],
) -> tuple[LetterStatus, ...]:
    """Merge two guesses letter by letter."""
    return tuple(merge(old, new) for old, new in zip(previous, incoming, strict=True))


__all__ = ["evaluate", "merge", "merge_results"]
