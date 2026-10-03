"""Loading, normalising and validating the two word lists."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from wordle.config import DEFAULT_CONFIG
from wordle.words import (
    ALPHABET,
    WordList,
    is_spelling,
    normalize,
    read_words,
)


class TestNormalize:
    def test_lowercases_and_trims(self) -> None:
        assert normalize("  GATO  ") == "gato"

    def test_drops_the_accent_off_the_vowels(self) -> None:
        assert normalize("CANCION") == "cancion"
        assert normalize("CANCIÓN") == "cancion"

    def test_keeps_the_enye_because_it_is_a_letter(self) -> None:
        """NFD would split ``ñ`` into ``n`` plus a combining tilde."""
        assert normalize("SEÑOR") == "señor"
        assert normalize("CAÑÓN") == "cañon"
        assert len(normalize("CAÑÓN")) == 5

    def test_folds_the_dieresis_in_guergenza(self) -> None:
        assert normalize("VERGÜENZA") == "verguenza"


class TestSpelling:
    def test_accepts_plain_letters_and_enye(self) -> None:
        assert is_spelling("señor")

    def test_rejects_digits_and_symbols(self) -> None:
        assert not is_spelling("12345")
        assert not is_spelling("a-b_c")

    def test_rejects_the_empty_word(self) -> None:
        assert not is_spelling("")

    def test_alphabet_has_twenty_seven_letters(self) -> None:
        assert len(ALPHABET) == 27


class TestReadWords:
    def test_skips_blanks_and_comments(self, tmp_path: Path) -> None:
        path = tmp_path / "words.txt"
        path.write_text("gato\n\n# una nota\nperro\n", encoding="utf-8")
        assert read_words(path) == ("gato", "perro")

    def test_missing_file_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_words(tmp_path / "nope.txt")


class TestWordList:
    def test_stores_normalised_and_deduplicated(self) -> None:
        words = WordList(["PERRO", "perro", " Llave "], ["perro", "llave"])
        assert words.secrets == ("perro", "llave")
        assert words.secret_count == 2

    def test_normalises_accents_on_the_way_in(self) -> None:
        words = WordList(["Limón"], ["limón", "perro"])
        assert words.secrets == ("limon",)

    def test_recognises_guesses_case_and_accent_insensitively(self) -> None:
        words = WordList(["limon"], ["limon", "perro"])
        assert words.is_valid("PERRO")
        assert words.is_valid(" Limón ")

    def test_rejects_words_outside_the_list(self) -> None:
        words = WordList(["perro"], ["perro", "llave"])
        assert not words.is_valid("verde")
        assert "verde" not in words

    def test_rejects_entries_of_the_wrong_length(self) -> None:
        with pytest.raises(ValueError, match="unusable"):
            WordList(["perro"], ["perro", "llave", "lluvia"])

    def test_rejects_entries_with_strange_characters(self) -> None:
        with pytest.raises(ValueError, match="unusable"):
            WordList(["perro"], ["perro", "12345"])

    def test_a_secret_must_also_be_a_legal_guess(self) -> None:
        with pytest.raises(ValueError, match="secret words absent"):
            WordList(["llave"], ["perro", "verde"])

    def test_empty_lists_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="secret word list is empty"):
            WordList([], ["perro"])
        with pytest.raises(ValueError, match="valid word list is empty"):
            WordList(["perro"], [])

    def test_random_secret_only_returns_a_secret(self) -> None:
        words = WordList(["perro", "llave"], ["perro", "llave", "verde"])
        picked = {words.random_secret(random.Random(seed)) for seed in range(20)}
        assert picked <= {"perro", "llave"}
        assert picked  # not empty after twenty draws

    def test_the_same_seed_deals_the_same_word(self) -> None:
        words = WordList(["perro", "llave", "verde"], ["perro", "llave", "verde"])
        first = words.random_secret(random.Random(7))
        second = words.random_secret(random.Random(7))
        assert first == second


@pytest.fixture(scope="module")
def shipped() -> WordList:
    """The real data files, loaded once for the whole module."""
    return WordList.from_files()


class TestRealDataFiles:
    """The shipped lists must obey the rules the engine relies on."""

    def test_every_secret_is_five_letters_of_the_alphabet(
        self,
        shipped: WordList,
    ) -> None:
        for word in shipped.secrets:
            assert len(word) == DEFAULT_CONFIG.word_length, word
            assert set(word) <= ALPHABET, word

    def test_there_are_enough_words_to_play(self, shipped: WordList) -> None:
        assert shipped.secret_count >= 200
        assert shipped.valid_count >= 500

    def test_the_dictionary_accepts_every_secret(self, shipped: WordList) -> None:
        for word in shipped.secrets:
            assert shipped.is_valid(word), word

    def test_the_enye_is_playable(self, shipped: WordList) -> None:
        assert any("ñ" in word for word in shipped.valid)
