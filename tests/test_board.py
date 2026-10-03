"""The grid: how it fills, when it is full, and when it refuses."""

from __future__ import annotations

import pytest

from wordle.board import Board, BoardFullError
from wordle.domain import Guess, LetterResult, LetterStatus

GREEN = LetterStatus.CORRECT


def guess(word: str = "gatos") -> Guess:
    """A guess with every letter marked green, for filling the grid."""
    return Guess(
        text=word,
        results=tuple(LetterResult(letter, GREEN) for letter in word),
    )


class TestEmptyBoard:
    def test_starts_empty_at_the_configured_size(self) -> None:
        board = Board(6, 5)
        assert board.rows == 6
        assert board.columns == 5
        assert board.is_empty
        assert not board.is_full

    def test_every_cell_starts_as_none(self) -> None:
        board = Board(2, 2)
        assert board.cell_at(0, 0) is None
        assert board.cell_at(1, 1) is None

    def test_rejects_a_degenerate_size(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            Board(0, 5)
        with pytest.raises(ValueError, match="at least one row"):
            Board(6, 0)


class TestFilling:
    def test_the_first_guess_lands_on_row_zero(self) -> None:
        board = Board(6, 5)
        assert board.add(guess()) == 0
        assert not board.is_empty
        assert board.used_rows == 1

    def test_guesses_stack_underneath_each_other(self) -> None:
        board = Board(6, 5)
        board.add(guess("gatos"))
        board.add(guess("perro"))
        assert [g.letters for g in board.guesses] == ["gatos", "perro"]
        assert board.cell_at(0, 0).letter == "g"
        assert board.cell_at(1, 0).letter == "p"

    def test_row_at_rebuilds_the_guess(self) -> None:
        board = Board(6, 5)
        board.add(guess("llama"))
        assert board.row_at(0).letters == "llama"
        assert board.row_at(0).is_win

    def test_reading_an_unfilled_row_is_an_error(self) -> None:
        board = Board(6, 5)
        with pytest.raises(IndexError, match="still empty"):
            board.row_at(0)

    def test_reading_a_row_off_the_board_is_an_error(self) -> None:
        board = Board(6, 5)
        with pytest.raises(IndexError, match="no row"):
            board.row_at(9)

    def test_reading_a_cell_off_the_board_is_an_error(self) -> None:
        board = Board(6, 5)
        with pytest.raises(IndexError, match="no cell"):
            board.cell_at(0, 5)


class TestCapacity:
    def test_six_guesses_fill_a_six_row_board(self) -> None:
        board = Board(6, 5)
        for _ in range(6):
            board.add(guess())
        assert board.is_full
        assert board.used_rows == 6

    def test_a_seventh_guess_is_refused(self) -> None:
        board = Board(6, 5)
        for _ in range(6):
            board.add(guess())
        with pytest.raises(BoardFullError):
            board.add(guess())

    def test_a_guess_of_the_wrong_width_is_refused(self) -> None:
        board = Board(6, 5)
        with pytest.raises(ValueError, match="needs 5 letters"):
            board.add(guess("gato"))
