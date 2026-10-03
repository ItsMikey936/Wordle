"""Remove words from a word list by hand.

python tools/prune.py data/valid_es.txt aloud aloof chasing ...
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wordle.words import normalize


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    path = Path(sys.argv[1])
    targets = {normalize(word) for word in sys.argv[2:]}
    kept: list[str] = []
    removed: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        is_word = stripped and not stripped.startswith("#")
        if is_word and normalize(stripped) in targets:
            removed.append(stripped)
            continue
        kept.append(line)

    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"{path.name}: removed {len(removed)} -> {' '.join(sorted(removed))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
