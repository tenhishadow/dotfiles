#!/usr/bin/env python3
"""Temporary fail-open hook while the narrow guard is being rewritten."""

import sys


def main() -> int:
    """Allow the tool call without attempting partial shell parsing."""
    sys.stdin.read()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
