"""Core domain model: letter marks, guesses and the game status.

This module knows nothing about files, randomness or Streamlit, which keeps
the rules easy to test in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LetterStatus(Enum):
    """The three marks a letter can earn after a guess."""

    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


#: How good each mark is, so the keyboard keeps the best one it has seen.
#: Green beats yellow beats grey, and a mark never travels backwards.
STATUS_PRIORITY: dict[LetterStatus, int] = {
    LetterStatus.ABSENT: 0,
    LetterStatus.PRESENT: 1,
    LetterStatus.CORRECT: 2,
}


class GameStatus(Enum):
    """Lifecycle of a single playthrough."""

    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass(frozen=True, slots=True)
class LetterResult:
    """One guessed letter and the mark it earned."""

    letter: str
    status: LetterStatus

    @property
    def is_correct(self) -> bool:
        return self.status is LetterStatus.CORRECT


@dataclass(frozen=True, slots=True)
class Guess:
    """A completed row: the word the player typed and its marks."""

    text: str
    results: tuple[LetterResult, ...]

    @property
    def is_win(self) -> bool:
        """True when every single letter landed on its spot."""
        return bool(self.results) and all(result.is_correct for result in self.results)

    @property
    def letters(self) -> str:
        return "".join(result.letter for result in self.results)

    @property
    def statuses(self) -> tuple[LetterStatus, ...]:
        return tuple(result.status for result in self.results)

    def __str__(self) -> str:
        return self.letters or self.text


__all__ = [
    "STATUS_PRIORITY",
    "GameStatus",
    "Guess",
    "LetterResult",
    "LetterStatus",
]
