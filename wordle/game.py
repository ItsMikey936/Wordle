"""The rules engine.

:class:`Game` is pure Python: it never imports Streamlit. The secret word and
the randomness are injected, so a test can replay the exact same game by
seeding the generator, and the board it drives knows nothing about colours.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import messages
from .board import Board
from .config import DEFAULT_CONFIG, WordleConfig
from .domain import GameStatus, Guess, LetterStatus
from .evaluator import evaluate, merge
from .words import WordList, is_spelling, normalize


@dataclass(frozen=True, slots=True)
class SubmitResult:
    """What happened when the player sent a guess.

    ``ok`` False means nothing moved: the attempt was rejected and the board is
    exactly as it was.
    """

    ok: bool
    message: str = ""
    guess: Guess | None = None


@dataclass
class Game:
    """One playthrough: a secret word, a board, and six chances."""

    words: WordList = field(default_factory=WordList.from_files)
    config: WordleConfig = DEFAULT_CONFIG
    seed: int | None = None

    rng: random.Random = field(init=False, repr=False)
    board: Board = field(init=False)
    status: GameStatus = field(init=False, default=GameStatus.PLAYING)
    secret: str = field(init=False)
    attempts_left: int = field(init=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.restart()

    # ------------------------------------------------------------------ setup

    def restart(self, seed: int | None = None) -> None:
        """Deal a brand new word, reusing this object and its board."""
        if seed is not None:
            self.seed = seed
            self.rng = random.Random(seed)
        self.secret = self.words.random_secret(self.rng)
        self.board = Board(self.config.rows, self.config.columns)
        self.status = GameStatus.PLAYING
        self.attempts_left = self.config.max_attempts

    # ------------------------------------------------------------------ state

    @property
    def is_over(self) -> bool:
        return self.status is not GameStatus.PLAYING

    @property
    def is_won(self) -> bool:
        return self.status is GameStatus.WON

    @property
    def guesses(self) -> tuple[Guess, ...]:
        return self.board.guesses

    @property
    def attempts_used(self) -> int:
        return self.config.max_attempts - self.attempts_left

    @property
    def revealed_secret(self) -> str:
        """The secret word, but only once the game is actually over."""
        return self.secret if self.is_over else ""

    # ----------------------------------------------------------------- submit

    def validate(self, raw: str) -> str:
        """Return why ``raw`` cannot be played, or an empty string if it can.

        The order matters for the message the player sees: length first, then
        spelling, then dictionary. ``"12345"`` is five characters long but not
        five letters, and the player deserves to be told which one it was.
        """
        word = normalize(raw)
        if len(word) != self.config.word_length:
            return messages.NOT_ENOUGH
        if not is_spelling(word):
            return messages.NOT_LETTERS
        if not self.words.is_valid(word):
            return messages.NOT_A_WORD.format(word=word)
        return ""

    def submit(self, raw: str) -> SubmitResult:
        """Play ``raw`` as the next attempt.

        A rejected guess costs nothing: no row, no mark, no attempt spent.
        """
        if self.is_over:
            return SubmitResult(ok=False, message=messages.GAME_ALREADY_OVER)

        complaint = self.validate(raw)
        if complaint:
            return SubmitResult(ok=False, message=complaint)

        word = normalize(raw)
        guess = Guess(text=word, results=evaluate(word, self.secret))
        self.board.add(guess)
        self.attempts_left -= 1

        if guess.is_win:
            self.status = GameStatus.WON
            return SubmitResult(
                ok=True,
                message=messages.victory(self.attempts_used),
                guess=guess,
            )
        if self.board.is_full:
            self.status = GameStatus.LOST
            return SubmitResult(
                ok=True,
                message=messages.defeat(self.secret),
                guess=guess,
            )
        return SubmitResult(ok=True, guess=guess)

    # ---------------------------------------------------------------- keyboard

    def keyboard_states(self) -> dict[str, LetterStatus]:
        """The best mark known for every letter the player has tried.

        Marks are merged in play order, so a letter never falls back to grey
        after a later guess placed it green.
        """
        states: dict[str, LetterStatus] = {}
        for guess in self.board.guesses:
            for result in guess.results:
                current = states.get(result.letter)
                states[result.letter] = (
                    result.status if current is None else merge(current, result.status)
                )
        return states

    def best_status(self, letter: str) -> LetterStatus | None:
        """The keyboard mark for one letter, or ``None`` if never tried."""
        return self.keyboard_states().get(normalize(letter))

    def is_known_absent(self, letter: str) -> bool:
        """True when the player can rule this letter out for good."""
        state = self.best_status(letter)
        return state is LetterStatus.ABSENT

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Game(status={self.status.value}, left={self.attempts_left})"


__all__ = ["Game", "SubmitResult"]
