"""Every tunable number of Wordle.

No other module defines gameplay constants: word length, attempt count and
where the word lists live all sit here, so the game can be rebalanced or
pointed at another language without touching a line of logic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class WordleConfig:
    """Single source of truth for the board size and the data files."""

    word_length: int = 5
    max_attempts: int = 6
    data_dir: Path = DATA_DIR
    secrets_file: str = "secrets_es.txt"
    valid_file: str = "valid_es.txt"

    @property
    def secrets_path(self) -> Path:
        return self.data_dir / self.secrets_file

    @property
    def valid_path(self) -> Path:
        return self.data_dir / self.valid_file

    @property
    def rows(self) -> int:
        """The board is ``rows`` tall: one row per allowed attempt."""
        return self.max_attempts

    @property
    def columns(self) -> int:
        return self.word_length

    def with_overrides(self, **overrides: object) -> WordleConfig:
        """Return a copy with some fields replaced."""
        return replace(self, **overrides)  # type: ignore[arg-type]


DEFAULT_CONFIG = WordleConfig()
