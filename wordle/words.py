"""Loading and validating the word lists.

The lists live in ``data/`` as plain text files, one word per line. Both are
normalised the same way the player's input is, so a list entry never has to
carry an accent: ``cancion`` accepts ``canción`` at the keyboard.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from pathlib import Path

from .config import DEFAULT_CONFIG, WordleConfig

#: The letters a Spanish guess may use: plain Latin plus ``ñ``, which is a
#: letter in its own right and never an accent.
ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyzñ")

#: Spanish vowels that may carry an accent. ``ñ`` is deliberately absent: it
#: decomposes into ``n`` + a combining tilde, so a naive strip would eat it.
#: Mapping the five vowels by hand keeps ``sueño`` five letters long.
VOWEL_ACCENTS = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }
)

COMMENT_PREFIX = "#"


def normalize(text: str) -> str:
    """Fold a raw word to the form the game compares.

    Lowercases, trims the edges and drops the accent off the vowels, leaving
    ``ñ`` untouched. ``"  CANCIÓN "`` becomes ``"cancion"``.
    """
    return text.strip().lower().translate(VOWEL_ACCENTS)


def is_spelling(word: str) -> bool:
    """True when every character is a letter this game accepts."""
    return bool(word) and set(word) <= ALPHABET


def read_words(path: Path) -> tuple[str, ...]:
    """Read one word per line, skipping blanks and ``#`` comments."""
    if not path.exists():
        raise FileNotFoundError(f"missing word list: {path}")
    words: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = normalize(line)
        if not entry or entry.startswith(COMMENT_PREFIX):
            continue
        words.append(entry)
    return tuple(words)


class WordList:
    """The two dictionaries: what can be guessed, and what can be the answer.

    Secrets are drawn from their own, smaller list; every guess is checked
    against the larger one. A secret is always a legal guess, so the player is
    never shown a board they cannot finish.
    """

    def __init__(
        self,
        secrets: Iterable[str],
        valid: Iterable[str],
        word_length: int = DEFAULT_CONFIG.word_length,
    ) -> None:
        self._word_length = word_length
        self._secrets = _unique(secrets, word_length)
        self._valid = _unique(valid, word_length)
        if not self._secrets:
            raise ValueError("the secret word list is empty")
        if not self._valid:
            raise ValueError("the valid word list is empty")
        missing = [word for word in self._secrets if word not in self._valid]
        if missing:
            raise ValueError(
                "secret words absent from the valid list: "
                + ", ".join(sorted(missing)[:5])
            )

    @classmethod
    def from_files(cls, config: WordleConfig = DEFAULT_CONFIG) -> WordList:
        """Load both lists from the data files named in ``config``."""
        return cls(
            secrets=read_words(config.secrets_path),
            valid=read_words(config.valid_path),
            word_length=config.word_length,
        )

    @property
    def secrets(self) -> tuple[str, ...]:
        return self._secrets

    @property
    def valid(self) -> tuple[str, ...]:
        return self._valid

    @property
    def secret_count(self) -> int:
        return len(self._secrets)

    @property
    def valid_count(self) -> int:
        return len(self._valid)

    def is_valid(self, word: str) -> bool:
        """True when ``word`` may be played as a guess."""
        return normalize(word) in self._valid

    def random_secret(self, rng: random.Random | None = None) -> str:
        """Pick the secret word for one playthrough."""
        chooser = rng or random
        return chooser.choice(self._secrets)

    def __contains__(self, word: object) -> bool:
        return isinstance(word, str) and self.is_valid(word)

    def __len__(self) -> int:
        return self.valid_count

    def __iter__(self) -> Iterator[str]:
        return iter(self._valid)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"WordList(secrets={self.secret_count}, valid={self.valid_count})"


def _unique(words: Iterable[str], word_length: int) -> tuple[str, ...]:
    """Normalise, drop anything misspelled, and keep the first occurrence."""
    seen: dict[str, None] = {}
    rejected: list[str] = []
    for raw in words:
        word = normalize(raw)
        if not is_spelling(word) or len(word) != word_length:
            rejected.append(raw)
            continue
        seen.setdefault(word, None)
    if rejected:
        raise ValueError(f"word list contains unusable entries: {rejected[:5]}")
    return tuple(seen)


__all__ = [
    "ALPHABET",
    "VOWEL_ACCENTS",
    "WordList",
    "is_spelling",
    "normalize",
    "read_words",
]
