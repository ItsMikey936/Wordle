"""The Streamlit layer, driven headlessly through Streamlit's own test client.

These tests import :mod:`app` through ``AppTest``, so they exercise the real
script: session state, the form, the rerun loop and the generated HTML.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui import KEYBOARD_ROWS
from wordle.words import read_words

APP = Path(__file__).resolve().parent.parent / "app.py"
VALID = read_words(APP.parent / "data" / "valid_es.txt")

GREEN = "#538d4e"
YELLOW = "#b59f3b"
GREY = "#3a3a3c"
UNTOUCHED = "#818384"


@pytest.fixture
def app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=30).run()


def markup(app: AppTest) -> str:
    """Everything the page rendered, minus the injected stylesheet."""
    return "\n".join(item.value for item in app.markdown).split("</style>")[-1]


def cells(app: AppTest) -> int:
    return markup(app).count('<td class="wl-cell')


def filled(app: AppTest) -> int:
    """How many tiles carry a letter, which is how many guesses were played."""
    return markup(app).count("wl-flip")


def key_colours(app: AppTest) -> list[str]:
    """The background of every keyboard key, in layout order."""
    page = markup(app)
    found: list[str] = []
    for chunk in page.split('class="wl-key"')[1:]:
        colour = chunk.split("background:")[1].split('"')[0].split(";")[0]
        found.append(colour)
    return found


def guess(app: AppTest, word: str) -> None:
    """Type a word, press the button, and let the rerun settle."""
    app.text_input[0].set_value(word)
    app.button[0].click().run()
    assert not app.exception, app.exception


class TestFirstRender:
    def test_it_loads_without_errors(self, app: AppTest) -> None:
        assert not app.exception
        assert app.title[0].value == "🟩 Wordle en español"

    def test_the_board_is_six_by_five_and_empty(self, app: AppTest) -> None:
        assert cells(app) == 30
        assert filled(app) == 0

    def test_the_keyboard_has_twenty_seven_letters(
        self,
        app: AppTest,
    ) -> None:
        assert len(key_colours(app)) == 27
        assert "ñ" in markup(app)

    def test_the_keyboard_starts_neutral(self, app: AppTest) -> None:
        assert set(key_colours(app)) == {UNTOUCHED}

    def test_it_shows_the_attempts_left(self, app: AppTest) -> None:
        assert [m.label for m in app.metric] == ["Intentos", "Usados"]
        assert app.metric[0].value == "6 / 6"


class TestRejectedGuess:
    def test_it_explains_the_length_rule(self, app: AppTest) -> None:
        guess(app, "gat")
        assert [e.value for e in app.error] == ["Introduce una palabra de 5 letras."]

    def test_it_costs_no_attempt_and_no_row(self, app: AppTest) -> None:
        guess(app, "gat")
        assert filled(app) == 0
        assert app.metric[0].value == "6 / 6"

    def test_it_rejects_non_letters(self, app: AppTest) -> None:
        guess(app, "12345")
        assert app.error[0].value == "Solo se admiten letras."

    def test_it_rejects_unknown_words(self, app: AppTest) -> None:
        guess(app, "xyzzy")
        assert "no está en el diccionario" in app.error[0].value


class TestPlaying:
    def test_a_real_guess_fills_one_row(self, app: AppTest) -> None:
        guess(app, "PERRO")
        assert filled(app) == 5
        assert app.metric[0].value == "5 / 6"
        assert app.metric[1].value == "1"

    def test_the_box_is_empty_again_after_a_guess(self, app: AppTest) -> None:
        guess(app, "PERRO")
        assert app.text_input[0].value == ""

    def test_the_keyboard_remembers_the_letters(self, app: AppTest) -> None:
        guess(app, "PERRO")
        colours = set(key_colours(app))
        assert colours != {UNTOUCHED}
        assert colours <= {GREEN, YELLOW, GREY, UNTOUCHED}


class TestEnding:
    def test_typing_the_secret_wins(self, app: AppTest) -> None:
        secret = app.session_state["game"].secret
        guess(app, secret)
        assert app.success
        assert "Encontrada" in app.success[0].value

    def test_a_win_hides_the_input_and_offers_a_new_game(
        self,
        app: AppTest,
    ) -> None:
        guess(app, app.session_state["game"].secret)
        assert not app.text_input
        assert any("Jugar otra vez" in b.label for b in app.button)

    def test_the_keyboard_is_all_green_after_a_win(self, app: AppTest) -> None:
        secret = app.session_state["game"].secret
        guess(app, secret)
        played = set(secret)
        layout = "".join(KEYBOARD_ROWS)
        assert set(key_colours(app)) <= {GREEN, UNTOUCHED}
        assert all(
            colour == GREEN
            for letter, colour in zip(layout, key_colours(app), strict=True)
            if letter in played
        )

    def test_six_wrong_guesses_reveal_the_answer(self, app: AppTest) -> None:
        secret = app.session_state["game"].secret
        for word in _wrong_words(secret):
            guess(app, word)
        assert any("La palabra era" in e.value for e in app.error)
        assert f"«{secret}»" in app.error[0].value
        assert filled(app) == 30

    def test_the_input_box_is_gone_once_over(self, app: AppTest) -> None:
        secret = app.session_state["game"].secret
        for word in _wrong_words(secret):
            guess(app, word)
        assert not app.text_input

    def test_play_again_deals_a_fresh_board(self, app: AppTest) -> None:
        secret = app.session_state["game"].secret
        for word in _wrong_words(secret):
            guess(app, word)
        again = next(b for b in app.button if "Jugar otra vez" in b.label)
        again.click().run()
        assert not app.exception
        assert filled(app) == 0
        assert app.metric[0].value == "6 / 6"
        assert set(key_colours(app)) == {UNTOUCHED}


def _wrong_words(secret: str) -> list[str]:
    """Six legal words, none of which is the secret."""
    wrong = [word for word in VALID if word != secret]
    assert len(wrong) >= 6
    return wrong[:6]
