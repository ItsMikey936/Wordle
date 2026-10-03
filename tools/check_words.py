"""Check the two word lists before trusting them.

Run it from the project root::

    python tools/check_words.py

It reports every entry that is not exactly five letters of ``a-z`` plus ``ñ``,
the words repeated inside a file, and any secret the dictionary would reject.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wordle.words import ALPHABET, normalize

DATA = Path(__file__).resolve().parent.parent / "data"
LENGTH = 5
TARGET_SECRETS = 250
TARGET_VALID = 1200


def load(path: Path) -> list[str]:
    return [
        normalize(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def inspect(path: Path) -> tuple[set[str], int]:
    """Print the problems in one file; return its good words and bad count."""
    words = load(path)
    bad_length = [(word, len(word)) for word in words if len(word) != LENGTH]
    bad_chars = [word for word in words if set(word) - ALPHABET]
    repeated = sorted(word for word, n in Counter(words).items() if n > 1)

    good = {word for word in words if len(word) == LENGTH and not set(word) - ALPHABET}

    print(f"\n=== {path.name}: {len(words)} entries, {len(good)} usable ===")
    if bad_length:
        print(f"  wrong length ({len(bad_length)}):")
        for word, size in sorted(bad_length, key=lambda pair: -pair[1]):
            print(f"    {word} -> {size}")
    if bad_chars:
        print(f"  illegal characters ({len(bad_chars)}):")
        for word in sorted(set(bad_chars)):
            stray = sorted(set(word) - ALPHABET)
            print(f"    {word} -> {stray}")
    if repeated:
        print(f"  repeated ({len(repeated)}): {' '.join(repeated)}")
    if not bad_length and not bad_chars and not repeated:
        print("  clean")

    return good, len(bad_length) + len(bad_chars)


def main() -> int:
    secrets, bad_secret = inspect(DATA / "secrets_es.txt")
    valid, bad_valid = inspect(DATA / "valid_es.txt")

    missing = sorted(secrets - valid)
    if missing:
        print(f"\nsecrets the dictionary rejects ({len(missing)}):")
        print("  " + " ".join(missing))

    print(
        f"\nsecrets={len(secrets)} (target {TARGET_SECRETS})  "
        f"valid={len(valid)} (target {TARGET_VALID})"
    )
    print(f"secrets carrying ñ: {sum('ñ' in word for word in secrets)}")
    print(f"valid carrying ñ:   {sum('ñ' in word for word in valid)}")

    problems = bad_secret + bad_valid + len(missing)
    if len(secrets) < TARGET_SECRETS:
        print(f"NOTE: {TARGET_SECRETS - len(secrets)} secrets still missing")
    if len(valid) < TARGET_VALID:
        print(f"NOTE: {TARGET_VALID - len(valid)} valid words still missing")
    print("RESULT:", "FAIL" if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
