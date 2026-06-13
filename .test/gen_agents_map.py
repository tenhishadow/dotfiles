#!/usr/bin/env python3
"""Generate the nested-AGENTS.md ownership list inside the root AGENTS.md.

The root AGENTS.md lists every nested AGENTS.md an editor must consult. That
list is the instruction-layer ownership map, and it drifts whenever a role or
area gains or loses an AGENTS.md. This generator rebuilds the list from the
filesystem (the single source of truth) and prints the full root AGENTS.md with
the generated block replaced, mirroring docs:nvim-keymaps.

    go-task docs:agents        # rewrite AGENTS.md in place
    go-task docs:agents:check  # fail if the committed list is stale

The companion reference check (check_instruction_refs.py) proves every listed
path exists; this generator proves every existing nested AGENTS.md is listed.
Together the ownership map cannot drift in either direction.
"""

from __future__ import annotations

import sys
from pathlib import Path

BEGIN = "<!-- BEGIN GENERATED: nested-agents (go-task docs:agents) -->"
END = "<!-- END GENERATED: nested-agents -->"

# Vendored / generated trees whose AGENTS.md files are not ours.
EXCLUDED_DIRS = (".venv", ".git", ".collections", ".ansible", ".task", "node_modules")


def repo_root() -> Path:
    """Return the repository root (parent of the .test directory)."""
    return Path(__file__).resolve().parent.parent


def nested_agents(root: Path) -> list[str]:
    """Return sorted repo-relative paths of every nested AGENTS.md."""
    paths = []
    for path in root.rglob("AGENTS.md"):
        if path == root / "AGENTS.md":
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        paths.append(str(path.relative_to(root)))
    return sorted(paths)


def render(root: Path) -> str:
    """Return the root AGENTS.md with the generated block refreshed."""
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("AGENTS.md is missing the nested-agents generator markers")
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    listing = "\n".join(f"  - `{path}`" for path in nested_agents(root))
    return f"{head}{BEGIN}\n{listing}\n  {END}{tail}"


def main() -> int:
    """Print the regenerated AGENTS.md to stdout."""
    sys.stdout.write(render(repo_root()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
