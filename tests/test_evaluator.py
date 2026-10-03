"""The scoring rules, with most of the weight on repeated letters."""

from __future__ import annotations

import pytest

from wordle.domain import LetterStatus as Status
from wordle.evaluator import evaluate, merge

CORRECT = Status.CORRECT
PRESENT = Status.PRESENT
ABSENT = Status.ABSENT


def marks(guess: str, secret: str) -> tuple[Status, ...]:
    """The tuple of marks, for writing expectations readably."""
    return tuple(result.status for result in evaluate(guess, secret))


class TestBasic:
    def test_all_green_on_an_exact_guess(self) -> None:
        assert marks("verde", "verde") == (CORRECT,) * 5

    def test_all_grey_when_nothing_matches(self) -> None:
        assert marks("perro", "silla") == (ABSENT,) * 5

    @pytest.mark.parametrize(
        ("guess", "secret", "expected"),
        [
            # R is green at its own spot; E is somewhere else in the secret.
            ("acert", "perro", (ABSENT, ABSENT, PRESENT, CORRECT, ABSENT)),
            # Four in place, then O which only exists elsewhere in "gallo".
            ("galos", "gallo", (CORRECT, CORRECT, CORRECT, PRESENT, ABSENT)),
            # Not one letter of "perro" appears anywhere in "silla".
            ("perro", "silla", (ABSENT, ABSENT, ABSENT, ABSENT, ABSENT)),
            # Two L yellow, A yellow, then the rest absent.
            ("llave", "gallo", (PRESENT, PRESENT, PRESENT, ABSENT, ABSENT)),
        ],
    )
    def test_mixed_marks(
        self,
        guess: str,
        secret: str,
        expected: tuple[Status, ...],
    ) -> None:
        assert marks(guess, secret) == expected

    def test_result_keeps_the_guessed_letter_in_place(self) -> None:
        results = evaluate("arroz", "arroz")
        assert [result.letter for result in results] == list("arroz")

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError, match="letter guess"):
            evaluate("gato", "gatos")


class TestRepeatedLetters:
    def test_green_wins_over_yellow_when_the_secret_has_one_copy(self) -> None:
        """``A`` is green at the end, so the earlier ``A`` cannot be yellow.

        The secret has a single ``A`` and the guess has two. Greens are spent
        first, so the second ``A`` has nothing left to claim.
        """
        assert marks("llama", "silla") == (
            PRESENT,
            PRESENT,
            ABSENT,
            ABSENT,
            CORRECT,
        )

    def test_three_of_a_letter_only_fill_the_copies_that_exist(self) -> None:
        """The secret has two ``R`` and two ``O``; the guess has three each."""
        assert marks("osoas", "arroz") == (
            PRESENT,
            ABSENT,
            ABSENT,
            PRESENT,
            ABSENT,
        )

    def test_a_green_in_the_middle_is_spent_before_the_yellows(self) -> None:
        """``R`` is green in the middle, leaving one ``R`` for the first."""
        assert marks("rrrpp", "perro") == (
            PRESENT,
            ABSENT,
            CORRECT,
            PRESENT,
            ABSENT,
        )

    def test_both_copies_can_be_yellow_when_none_is_green(self) -> None:
        """Two ``L`` in the secret, neither in its own spot: both go yellow."""
        assert marks("nolla", "lleno") == (
            PRESENT,
            PRESENT,
            PRESENT,
            PRESENT,
            ABSENT,
        )

    def test_a_repeated_letter_only_claims_the_copies_that_exist(self) -> None:
        """The secret holds a single ``A``, so three of them cannot all mark."""
        assert marks("aaaaa", "arroz") == (
            CORRECT,
            ABSENT,
            ABSENT,
            ABSENT,
            ABSENT,
        )

    def test_greens_never_exceed_the_secret_supply(self) -> None:
        """The secret has four ``A``; a fifth one must stay grey."""
        assert marks("aaaaa", "aacaa") == (
            CORRECT,
            CORRECT,
            ABSENT,
            CORRECT,
            CORRECT,
        )

    def test_one_green_plus_one_yellow_uses_exactly_two_copies(self) -> None:
        """``SILLA`` has two ``L``: one is green, the other only yellow."""
        assert marks("llalo", "silla") == (
            PRESENT,
            ABSENT,
            PRESENT,
            CORRECT,
            ABSENT,
        )


class TestEnye:
    def test_enye_and_n_are_different_letters(self) -> None:
        assert marks("canon", "cañón") == (
            CORRECT,
            CORRECT,
            ABSENT,
            CORRECT,
            CORRECT,
        )

    def test_enye_is_marked_but_a_bare_n_is_not(self) -> None:
        """The secret has one ``ñ`` and no plain ``n``, so only ``ñ`` marks."""
        assert marks("esnoñ", "señor") == (
            PRESENT,
            PRESENT,
            ABSENT,
            CORRECT,
            PRESENT,
        )


class TestNormalisation:
    def test_uppercase_and_accents_are_folded_away(self) -> None:
        assert marks("  PÉRRO ", "perro") == (CORRECT,) * 5

    def test_two_different_spellings_score_the_same(self) -> None:
        assert marks("CANCION", "cancion") == marks("cancion", "cancion")


class TestMerge:
    def test_green_beats_yellow(self) -> None:
        assert merge(PRESENT, CORRECT) is CORRECT

    def test_yellow_beats_grey(self) -> None:
        assert merge(ABSENT, PRESENT) is PRESENT

    def test_a_mark_never_goes_backwards(self) -> None:
        assert merge(CORRECT, ABSENT) is CORRECT
        assert merge(PRESENT, ABSENT) is PRESENT

    def test_merging_a_mark_with_itself_is_stable(self) -> None:
        for status in Status:
            assert merge(status, status) is status
