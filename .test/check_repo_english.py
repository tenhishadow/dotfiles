#!/usr/bin/env python3
"""Enforce the English-only repository-text rule mechanically.

AGENTS.md requires repository text, comments, task names, docs, and AI
instructions to stay in English (quoted external output excepted). This is a
regression guard, not a language detector: it flags non-ASCII *letters*
(Unicode category L*), which reliably catches the common failure mode of
Cyrillic or other non-Latin prose slipping into committed files. Non-ASCII
symbol glyphs that terminal configs legitimately use -- Powerline icons, git
ahead/behind arrows, box-drawing, zero-width spaces -- are categories S*/C* and
are intentionally not flagged.

Binary blobs are skipped (NUL-byte heuristic, matching git). ALLOWLIST holds
paths that legitimately carry non-ASCII letters (for example quoted external
output or a transliterated proper noun). Run with plain Python:

    python3 .test/check_repo_english.py
"""

from __future__ import annotations

import subprocess
import sys
import unicodedata
from pathlib import Path

# Tracked paths permitted to contain non-ASCII (e.g. quoted external output).
# Keep this list narrow and justify each entry; an empty list keeps the guard
# strict for the whole tree.
ALLOWLIST: frozenset[str] = frozenset()


def tracked_files() -> list[str]:
    """Return repository-tracked file paths via git."""
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def first_foreign_letter(data: bytes) -> tuple[int, str] | None:
    """Return (line, char) of the first non-ASCII letter, or None.

    Non-ASCII symbols (Powerline/Nerd Font glyphs, arrows, box-drawing,
    zero-width spaces) are categories S*/C* and pass; only non-Latin letters
    (category L*) count as non-English text.
    """
    if b"\x00" in data:
        return None  # binary blob, skip like git does
    text = data.decode("utf-8", errors="replace")
    line = 1
    for char in text:
        if char == "\n":
            line += 1
        elif ord(char) > 0x7F and unicodedata.category(char).startswith("L"):
            return line, char
    return None


def main() -> int:
    """Scan tracked text files and report non-ASCII content."""
    problems = []
    for rel in tracked_files():
        if rel in ALLOWLIST:
            continue
        path = Path(rel)
        if not path.is_file():
            continue
        found = first_foreign_letter(path.read_bytes())
        if found is not None:
            line, char = found
            problems.append(
                f"{rel}:{line}: non-English letter {char!r} (U+{ord(char):04X}) in committed file"
            )

    if problems:
        print("non-English text in tracked files:")
        for problem in problems:
            print(f"  {problem}")
        print("  (allowlist quoted external output / proper nouns in ALLOWLIST if intentional)")
        return 1
    print("repository text is free of non-English letters (English-only guard passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
