"""The grid the player fills in, one guess per row."""

from __future__ import annotations

from .domain import Guess, LetterResult


class BoardFullError(RuntimeError):
    """Raised when a seventh guess is forced into a six-row board."""


class Board:
    """A fixed ``rows`` x ``columns`` grid that only ever fills downwards.

    Empty cells hold ``None``; the board knows its own size but nothing about
    colours, words or whether a guess was any good.
    """

    def __init__(self, rows: int, columns: int) -> None:
        if rows < 1 or columns < 1:
            raise ValueError("a board needs at least one row and one column")
        self._rows = rows
        self._columns = columns
        self._cells: list[list[LetterResult | None]] = [
            [None] * columns for _ in range(rows)
        ]

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def columns(self) -> int:
        return self._columns

    @property
    def used_rows(self) -> int:
        """How many rows are already taken."""
        return sum(1 for row in self._cells if row[0] is not None)

    @property
    def is_full(self) -> bool:
        return self.used_rows >= self._rows

    @property
    def is_empty(self) -> bool:
        return self.used_rows == 0

    @property
    def guesses(self) -> tuple[Guess, ...]:
        """Every guess played so far, oldest first."""
        return tuple(self.row_at(index) for index in range(self.used_rows))

    def next_row_index(self) -> int:
        """The row the next guess will land on."""
        return self.used_rows

    def add(self, guess: Guess) -> int:
        """Place ``guess`` on the first free row and return that row's index."""
        if self.is_full:
            raise BoardFullError(f"the board already holds {self._rows} guesses")
        if len(guess.results) != self._columns:
            raise ValueError(
                f"a guess needs {self._columns} letters, got {len(guess.results)}"
            )
        index = self.used_rows
        self._cells[index] = list(guess.results)
        return index

    def row_at(self, index: int) -> Guess:
        """Rebuild the :class:`Guess` sitting in row ``index``."""
        if not 0 <= index < self._rows:
            raise IndexError(f"no row {index} on a {self._rows}-row board")
        cells = self._cells[index]
        if cells[0] is None:
            raise IndexError(f"row {index} is still empty")
        filled = tuple(cell for cell in cells if cell is not None)
        return Guess(text="".join(cell.letter for cell in filled), results=filled)

    def cell_at(self, row: int, column: int) -> LetterResult | None:
        """The marked letter in one cell, or ``None`` if the cell is empty."""
        if not 0 <= row < self._rows or not 0 <= column < self._columns:
            raise IndexError(f"no cell ({row}, {column}) on this board")
        return self._cells[row][column]

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Board({self._rows}x{self._columns}, used={self.used_rows})"


__all__ = ["Board", "BoardFullError"]
