"""Add candidate words to a word list, keeping only the usable ones.

The point is convenience: candidates can be dumped in any format (one per
line, several per line, with commas or accents) and only the entries that are
exactly five letters of ``a-z`` plus ``ñ`` get appended.

    python tools/ingest.py data/valid_es.txt scratch.txt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wordle.words import ALPHABET, normalize

LENGTH = 5
SPLIT = re.compile(r"[^a-zA-ZñÑáéíóúüÁÉÍÓÚÜ]+")


def candidates(text: str) -> list[str]:
    """Pull every plausible word out of a messy block of text."""
    found: list[str] = []
    for chunk in SPLIT.split(text):
        word = normalize(chunk)
        if len(word) == LENGTH and not set(word) - ALPHABET:
            found.append(word)
    return found


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    target, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    existing = {
        normalize(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    words = candidates(scratch.read_text(encoding="utf-8"))
    fresh: list[str] = []
    seen = set(existing)
    for word in words:
        if word not in seen:
            seen.add(word)
            fresh.append(word)

    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"\n# --- añadidos por ingest ({len(fresh)})\n")
        for word in fresh:
            handle.write(word + "\n")

    print(f"{target.name}: +{len(fresh)} words (total {len(seen)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
