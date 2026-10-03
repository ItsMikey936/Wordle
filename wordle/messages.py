"""Every string the player reads.

Keeping the wording in one module means the rules never decide how to phrase a
complaint, and the game can be translated without touching game logic.
"""

from __future__ import annotations

TITLE = "🟩 Wordle en español"
SUBTITLE = (
    "Adivina la palabra de 5 letras. Tienes 6 intentos. "
    "Cada intento te dice si una letra está bien puesta, si está en la "
    "palabra pero en otro sitio, o si no está."
)

INTRO = (
    "- 🟩 **Verde**: la letra es correcta y está en su sitio.\n"
    "- 🟨 **Amarillo**: la letra está en la palabra, pero en otro sitio.\n"
    "- ⬛ **Gris**: la letra no está en la palabra.\n"
    "- Si una letra se repite, solo se marca tantas veces como aparece en la "
    "palabra secreta."
)

NOT_ENOUGH = "Introduce una palabra de 5 letras."
NOT_LETTERS = "Solo se admiten letras."
NOT_A_WORD = "«{word}» no está en el diccionario."
GAME_ALREADY_OVER = "La partida ha terminado. Pulsa «Jugar otra vez»."
ATTEMPTS_LEFT = "Intentos restantes: {left}"

KEYBOARD_LEGEND = (
    "Teclado con el mejor estado conocido de cada letra (verde > amarillo > gris)."
)


def victory(attempts: int) -> str:
    """Celebrate a win, singular or plural depending on how fast it was."""
    tries = "intento" if attempts == 1 else "intentos"
    return f"¡Encontrada en {attempts} {tries}! 🎉"


def defeat(secret: str) -> str:
    """Announce a loss and hand over the word that was hiding."""
    return f"La palabra era «{secret}». Menos mal la siguiente será otra."


__all__ = [
    "ATTEMPTS_LEFT",
    "GAME_ALREADY_OVER",
    "INTRO",
    "KEYBOARD_LEGEND",
    "NOT_A_WORD",
    "NOT_ENOUGH",
    "NOT_LETTERS",
    "SUBTITLE",
    "TITLE",
    "defeat",
    "victory",
]
