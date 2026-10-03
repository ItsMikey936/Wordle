"""The rules engine: attempts, validation, endings and the keyboard."""

from __future__ import annotations

import pytest
from conftest import SECRETS, VALID, make_game

from wordle import messages
from wordle.domain import GameStatus
from wordle.domain import LetterStatus as Status
from wordle.game import Game
from wordle.words import WordList

GREEN = Status.CORRECT
YELLOW = Status.PRESENT
GREY = Status.ABSENT


class TestSetup:
    def test_deals_a_five_letter_secret_and_six_attempts(self) -> None:
        game = make_game()
        assert len(game.secret) == 5
        assert game.attempts_left == 6
        assert game.status is GameStatus.PLAYING
        assert game.board.is_empty

    def test_the_same_seed_replays_the_same_game(self) -> None:
        assert make_game().secret == make_game().secret

    def test_restart_hands_the_attempts_back(self) -> None:
        game = make_game()
        game.submit("perro")
        game.restart(seed=999)
        assert game.attempts_left == 6
        assert game.board.is_empty
        assert game.status is GameStatus.PLAYING


class TestValidation:
    @pytest.mark.parametrize("bad", ["", "   ", "perr", "perros", "perroo"])
    def test_wrong_length_is_rejected(self, bad: str) -> None:
        assert make_game().validate(bad) == messages.NOT_ENOUGH

    @pytest.mark.parametrize("bad", ["12345", "p3rr0", "perr!", "per.o"])
    def test_non_letters_are_rejected(self, bad: str) -> None:
        assert make_game().validate(bad) == messages.NOT_LETTERS

    def test_a_word_outside_the_dictionary_is_rejected(self) -> None:
        game = make_game("rival")
        assert game.validate("bruja") == messages.NOT_A_WORD.format(word="bruja")

    def test_a_real_word_is_accepted(self) -> None:
        assert make_game().validate("PERRO") == ""

    def test_accents_do_not_break_the_rule(self) -> None:
        assert make_game().validate(" Limón ") == ""


class TestRejectedGuessesCostNothing:
    def test_the_board_does_not_move(self) -> None:
        game = make_game()
        result = game.submit("perr")
        assert not result.ok
        assert result.guess is None
        assert game.board.is_empty
        assert game.attempts_left == 6

    def test_an_unknown_word_is_also_free(self) -> None:
        game = make_game()
        assert not game.submit("xyzzy").ok
        assert game.attempts_left == 6

    def test_a_rejected_guess_is_still_reported(self) -> None:
        assert make_game().submit("perr").message == messages.NOT_ENOUGH


class TestPlaying:
    def test_a_good_guess_spends_one_attempt_and_one_row(self) -> None:
        game = make_game("rival")
        result = game.submit("perro")
        assert result.ok
        assert result.guess is not None
        assert game.attempts_left == 5
        assert game.attempts_used == 1
        assert game.board.used_rows == 1

    def test_the_marks_reach_the_board(self) -> None:
        game = make_game("rival")
        game.submit("llama")
        assert game.board.row_at(0).statuses == (
            YELLOW,
            GREY,
            YELLOW,
            GREY,
            GREY,
        )

    def test_guesses_are_stored_in_order(self) -> None:
        game = make_game()
        game.submit("perro")
        game.submit("llama")
        assert [g.letters for g in game.guesses] == ["perro", "llama"]

    def test_typed_case_and_surrounding_space_are_folded_away(self) -> None:
        game = make_game()
        result = game.submit("  LLAMA ")
        assert result.guess is not None
        assert result.guess.letters == "llama"


class TestWinning:
    def test_guessing_the_secret_wins(self) -> None:
        game = make_game("rival")
        result = game.submit("rival")
        assert game.status is GameStatus.WON
        assert game.is_won
        assert result.message == messages.victory(1)

    def test_winning_on_the_last_attempt_still_wins(self) -> None:
        game = make_game("rival")
        for _ in range(5):
            assert game.submit("perro").ok
        assert game.attempts_left == 1
        game.submit("rival")
        assert game.status is GameStatus.WON
        assert game.attempts_left == 0

    def test_a_win_reveals_the_secret(self) -> None:
        game = make_game("rival")
        assert game.revealed_secret == ""
        game.submit("rival")
        assert game.revealed_secret == "rival"


class TestLosing:
    def test_six_wrong_guesses_lose_the_game(self) -> None:
        game = make_game("rival")
        for _ in range(6):
            assert game.submit("perro").ok
        assert game.status is GameStatus.LOST
        assert game.is_over
        assert game.attempts_left == 0

    def test_the_answer_is_revealed_on_a_loss(self) -> None:
        game = make_game("rival")
        for _ in range(6):
            result = game.submit("perro")
        assert result.message == messages.defeat("rival")
        assert game.revealed_secret == "rival"

    def test_the_board_still_shows_all_six_rows(self) -> None:
        game = make_game("rival")
        for _ in range(6):
            game.submit("perro")
        assert game.board.is_full

    def test_nothing_is_accepted_after_the_game_ends(self) -> None:
        game = make_game("rival")
        for _ in range(6):
            game.submit("perro")
        result = game.submit("rival")
        assert not result.ok
        assert result.message == messages.GAME_ALREADY_OVER
        assert game.status is GameStatus.LOST


class TestRestart:
    def test_clears_the_board_and_the_keyboard(self) -> None:
        game = make_game()
        for _ in range(3):
            game.submit("perro")
        assert game.keyboard_states()
        game.restart()
        assert game.board.is_empty
        assert game.attempts_left == 6
        assert game.status is GameStatus.PLAYING
        assert game.keyboard_states() == {}

    def test_a_new_game_can_deal_a_different_secret(self) -> None:
        game = Game(words=WordList(SECRETS, VALID), seed=1)
        seen = {game.secret}
        for seed in range(2, 40):
            game.restart(seed=seed)
            seen.add(game.secret)
        assert len(seen) > 1


class TestKeyboard:
    def test_an_untried_letter_has_no_mark(self) -> None:
        assert make_game().best_status("x") is None

    def test_letters_are_marked_from_the_guesses(self) -> None:
        game = make_game("llave")
        game.submit("perro")
        assert game.best_status("e") is YELLOW
        assert game.best_status("p") is GREY

    def test_a_green_stays_green_through_the_whole_game(self) -> None:
        game = make_game("arroz")
        game.submit("arroz")
        game.submit("llave")
        assert game.best_status("r") is GREEN

    def test_a_green_from_an_earlier_guess_survives_a_later_grey(self) -> None:
        """Greying a letter later must not undo a green it already earned."""
        game = make_game("arroz")
        game.submit("arroz")
        assert game.best_status("r") is GREEN
        game.submit("llave")
        assert game.best_status("r") is GREEN

    def test_a_green_upgrades_an_earlier_yellow(self) -> None:
        game = make_game("llave")
        game.submit("arbol")
        assert game.best_status("a") is YELLOW
        game.submit("llave")
        assert game.best_status("a") is GREEN

    def test_a_known_absent_letter_can_be_ruled_out(self) -> None:
        game = make_game("llave")
        game.submit("perro")
        assert game.is_known_absent("p")
        assert not game.is_known_absent("a")

    def test_uppercase_letters_are_folded_away(self) -> None:
        game = make_game("llave")
        game.submit("perro")
        assert game.best_status("E") is YELLOW
