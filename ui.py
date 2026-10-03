"""Streamlit presentation layer.

This is the only module that imports Streamlit. It draws whatever
:class:`wordle.game.Game` holds and forwards the player's word to it; the
engine never calls back here. The state lives in ``st.session_state``, and a
plain HTML table does the colouring because Streamlit has no native grid.
"""

from __future__ import annotations

import html

import streamlit as st

from wordle import messages
from wordle.domain import LetterStatus
from wordle.game import Game

STATE_KEY = "game"
FEEDBACK_KEY = "feedback"
SERIAL_KEY = "serial"

#: The three marks, plus the empty tile and the default key colour.
COLOURS: dict[LetterStatus, str] = {
    LetterStatus.CORRECT: "#538d4e",
    LetterStatus.PRESENT: "#b59f3b",
    LetterStatus.ABSENT: "#3a3a3c",
}
EMPTY_TILE = "#121213"
DEFAULT_KEY = "#818384"

#: Three rows, 27 letters: the plain alphabet plus ``ñ``.
KEYBOARD_ROWS: tuple[str, ...] = (
    "qwertyuiop",
    "asdfghjklñ",
    "zxcvbnm",
)

STYLES = """
<style>
.wl-board {
    border-collapse: separate;
    border-spacing: 5px;
    margin: 0 auto;
}
.wl-cell {
    width: 52px;
    height: 52px;
    border: 2px solid #3a3a3c;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #fff;
}
.wl-cell.wl-flip { animation: wl-pop .18s ease-in-out; }
@keyframes wl-pop {
    0% { transform: scale(.85); opacity: .5; }
    100% { transform: scale(1); opacity: 1; }
}
.wl-keys { text-align: center; margin-top: 1.4rem; }
.wl-keyrow { margin-bottom: 6px; }
.wl-key {
    display: inline-block;
    width: 40px;
    padding: 9px 0;
    margin: 0 2px;
    border-radius: 4px;
    font-size: .95rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #fff;
}
.wl-note { text-align: center; opacity: .65; font-size: .8rem; }
.wl-flash { animation: wl-fade 1.6s ease-out; }
@keyframes wl-fade { from { opacity: 1; } to { opacity: 0; } }
</style>
"""


def key_colour(status: LetterStatus | None) -> str:
    """The fill for one keyboard key: its best mark, or the neutral grey."""
    return COLOURS[status] if status is not None else DEFAULT_KEY


class StreamlitUI:
    """Renders Wordle and keeps the game in session state."""

    def __init__(self) -> None:
        if STATE_KEY not in st.session_state:
            self.new_game()
        self.game: Game = st.session_state[STATE_KEY]

    def new_game(self) -> None:
        """Deal a fresh word, discarding whatever the last one was."""
        st.session_state[STATE_KEY] = Game()
        st.session_state[FEEDBACK_KEY] = None
        st.session_state[SERIAL_KEY] = 0

    # ------------------------------------------------------------------ render

    def render(self) -> None:
        """Draw whichever screen the current state calls for."""
        st.set_page_config(
            page_title="Wordle ES",
            page_icon="🟩",
            layout="centered",
        )
        st.markdown(STYLES, unsafe_allow_html=True)

        st.title(messages.TITLE)
        st.caption(messages.SUBTITLE)

        self.render_board()
        self.render_keyboard()
        st.divider()

        if self.game.is_over:
            self.render_end()
        else:
            self.render_input()

    def render_board(self) -> None:
        """The 6x5 grid: played rows coloured, the rest still empty."""
        st.markdown(self._board_html(), unsafe_allow_html=True)

    def render_keyboard(self) -> None:
        """The on-screen keyboard, coloured with the best known mark."""
        states = self.game.keyboard_states()
        rows = []
        for row in KEYBOARD_ROWS:
            keys = "".join(self._key(letter, states) for letter in row)
            rows.append(f'<div class="wl-keyrow">{keys}</div>')
        block = f'<div class="wl-keys">{"".join(rows)}</div>'
        st.markdown(block, unsafe_allow_html=True)
        st.caption(messages.KEYBOARD_LEGEND)

    def render_input(self) -> None:
        """Attempts left, the last complaint, and the box to type a word in."""
        left, _spacer, used = st.columns([1, 2, 1])
        with left:
            st.metric(
                "Intentos",
                f"{self.game.attempts_left} / {self.game.config.max_attempts}",
            )
        with used:
            st.metric("Usados", self.game.attempts_used)

        self._render_feedback()

        # The box carries the attempt number in its key: a fresh key is an
        # empty box, which is the only way to clear a widget that has already
        # been rendered this run.
        serial = st.session_state.get(SERIAL_KEY, 0)
        with st.form(key=f"guess-{serial}"):
            word = st.text_input(
                "Tu intento",
                key=f"guess-word-{serial}",
                max_chars=self.game.config.word_length,
                placeholder="cinco letras",
            )
            submitted = st.form_submit_button("Intentar", type="primary")

        if submitted:
            self._submit(word)

    def render_end(self) -> None:
        """Win or loss, with the answer revealed and a way to play again."""
        if self.game.is_won:
            st.success(messages.victory(self.game.attempts_used))
        else:
            st.error(messages.defeat(self.game.revealed_secret))
        st.button("🎲 Jugar otra vez", on_click=self.new_game, type="primary")

    # ----------------------------------------------------------------- helpers

    def _submit(self, word: str) -> None:
        """Send the typed word to the engine, narrate it, and redraw."""
        result = self.game.submit(word)
        st.session_state[SERIAL_KEY] = st.session_state.get(SERIAL_KEY, 0) + 1
        if result.message and not self.game.is_over:
            # Only complaints and progress are worth stashing. The end screen
            # narrates the winning or losing word itself.
            st.session_state[FEEDBACK_KEY] = (
                result.message,
                "success" if result.ok else "error",
            )
        st.rerun()

    def _render_feedback(self) -> None:
        """Show whatever the last submission had to say."""
        stored = st.session_state.get(FEEDBACK_KEY)
        if not stored:
            return
        message, tone = stored
        getattr(st, tone)(message)
        st.session_state[FEEDBACK_KEY] = None

    def _board_html(self) -> str:
        cells: list[str] = []
        board = self.game.board
        for row in range(board.rows):
            for column in range(board.columns):
                result = board.cell_at(row, column)
                if result is None:
                    cells.append(
                        f'<td class="wl-cell" style="background:{EMPTY_TILE}"></td>'
                    )
                    continue
                colour = COLOURS[result.status]
                letter = html.escape(result.letter.upper())
                cells.append(
                    f'<td class="wl-cell wl-flip" style="background:{colour}">'
                    f"{letter}</td>"
                )

        rows = "".join(
            "<tr>"
            + "".join(cells[index * board.columns : (index + 1) * board.columns])
            + "</tr>"
            for index in range(board.rows)
        )
        return f'<table class="wl-board"><tbody>{rows}</tbody></table>'

    def _key(self, letter: str, states: dict[str, LetterStatus]) -> str:
        colour = key_colour(states.get(letter))
        return (
            f'<span class="wl-key" style="background:{colour}">'
            f"{html.escape(letter)}</span>"
        )


def main() -> None:
    StreamlitUI().render()


__all__ = ["COLOURS", "KEYBOARD_ROWS", "StreamlitUI", "main"]
