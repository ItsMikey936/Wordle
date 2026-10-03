"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import pytest

from wordle.game import Game
from wordle.words import WordList

#: Real five-letter words used to drive whole games without touching disk.
SECRETS = ("llave", "silla", "rival", "verde", "perro")
VALID = (
    *SECRETS,
    "llama",
    "gallo",
    "arana",
    "lleno",
    "raton",
    "arroz",
    "arbol",
    "gasto",
    "bravo",
    "monte",
    "limon",
    "senor",
)


@pytest.fixture
def words() -> WordList:
    """A tiny dictionary, so tests do not depend on the data files."""
    return WordList(SECRETS, VALID)


def make_game(secret: str = "rival") -> Game:
    """A game that is guaranteed to have been dealt ``secret``.

    The secret list holds that one word and nothing else, so the game is
    deterministic whatever the seed turns out to be.
    """
    return Game(words=WordList([secret], VALID), seed=1234)
