"""Wordle: a five-letter word guessing game.

The engine is pure Python and lives in these modules:

- :mod:`wordle.domain` — the marks, the guesses and the status enum.
- :mod:`wordle.evaluator` — the pure function that scores a guess.
- :mod:`wordle.board` — the grid guesses land on.
- :mod:`wordle.words` — loading and normalising the two word lists.
- :mod:`wordle.game` — the rules engine that ties them together.

Streamlit only ever shows up in ``ui.py`` at the project root.
"""

from __future__ import annotations

from .board import Board, BoardFullError
from .config import DEFAULT_CONFIG, WordleConfig
from .domain import (
    STATUS_PRIORITY,
    GameStatus,
    Guess,
    LetterResult,
    LetterStatus,
)
from .evaluator import evaluate, merge
from .game import Game, SubmitResult
from .words import WordList, is_spelling, normalize

__all__ = [
    "DEFAULT_CONFIG",
    "STATUS_PRIORITY",
    "Board",
    "BoardFullError",
    "Game",
    "GameStatus",
    "Guess",
    "LetterResult",
    "LetterStatus",
    "SubmitResult",
    "WordList",
    "WordleConfig",
    "evaluate",
    "is_spelling",
    "merge",
    "normalize",
]
