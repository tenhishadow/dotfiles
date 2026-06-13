#!/usr/bin/env python3
"""Fail when instruction docs reference things that no longer exist.

The instruction layer (AGENTS.md files, Copilot instructions, README, docs)
names go-task targets, roles, playbooks, and repository paths. When a target is
renamed or a file is removed, those references silently rot. This check parses
the docs and asserts that every reference resolves:

  * ``go-task <name>`` -> a real task key in Taskfile.yml (bare ``go-task`` is
    the default task).
  * repository paths anchored at a known top-level entry (roles/, inventory/,
    docs/, dotfiles/, .github/, .test/, playbook_*.yml, and tracked root files)
    -> the path (or its glob) exists.

System paths (/etc/...), URLs (brave://...), and home paths (~/...) are not
repository references and are ignored. Run with plain Python:

    python3 .test/check_instruction_refs.py
"""

from __future__ import annotations

import re
from pathlib import Path

# Files that make up the instruction / documentation layer.
DOC_GLOBS = (
    "AGENTS.md",
    "*/AGENTS.md",
    "**/AGENTS.md",
    "README.md",
    ".github/copilot-instructions.md",
    ".github/instructions/*.instructions.md",
    "docs/*.md",
)

# Top-level repository entries a path reference may be anchored at.
ANCHORS = ("roles/", "inventory/", "docs/", "dotfiles/", ".github/", ".test/")

# Vendored / generated trees that are not part of the instruction layer.
EXCLUDED_DIRS = (".venv", ".git", ".collections", ".ansible", ".task", "node_modules")

# Match go-task only at a command boundary (line start or inside backticks) so
# package lists like "pacman ... git go-task uv" are not read as invocations.
GO_TASK_RE = re.compile(
    r"(?:^[ \t$]*|`)go-task(?:\s+(?P<name>[a-z][a-z0-9:_-]*))?", re.M
)
# Backtick- or link-quoted tokens that look like repository paths.
TOKEN_RE = re.compile(r"[`(]([A-Za-z0-9][A-Za-z0-9._/*-]+)[`)]")
PLAYBOOK_RE = re.compile(r"\bplaybook_[a-z_]+\.yml\b")


def repo_root() -> Path:
    """Return the repository root (parent of the .test directory)."""
    return Path(__file__).resolve().parent.parent


def taskfile_task_names(root: Path) -> set[str]:
    """Return the set of task names declared in Taskfile.yml.

    Task names are the two-space-indented keys under the top-level ``tasks:``
    mapping. Parsed without a YAML dependency so the guard runs under plain
    Python like the other reports.
    """
    names: set[str] = set()
    in_tasks = False
    for raw in (root / "Taskfile.yml").read_text(encoding="utf-8").splitlines():
        if re.match(r"^\S", raw):  # any top-level key ends the tasks block
            in_tasks = raw.startswith("tasks:")
            continue
        if not in_tasks:
            continue
        match = re.match(r"^  ([A-Za-z][A-Za-z0-9:_-]*):\s*$", raw)
        if match:
            names.add(match.group(1))
    return names


def doc_files(root: Path) -> list[Path]:
    """Return the deduplicated instruction/documentation files."""
    found: set[Path] = set()
    for pattern in DOC_GLOBS:
        for path in root.glob(pattern):
            if path.is_file() and not any(part in EXCLUDED_DIRS for part in path.parts):
                found.add(path)
    return sorted(found)


def path_exists(root: Path, ref: str) -> bool:
    """Return whether a repo-relative reference (possibly a glob) resolves."""
    ref = ref.rstrip("/")
    if "*" in ref:
        return any(root.glob(ref))
    return (root / ref).exists()


def check_go_tasks(text: str, tasks: set[str]) -> list[str]:
    """Return go-task references that do not resolve to a real task."""
    problems = []
    for match in GO_TASK_RE.finditer(text):
        name = match.group("name")
        if name is not None and name not in tasks:
            problems.append(f"unknown go-task target: go-task {name}")
    return problems


def check_paths(root: Path, text: str) -> list[str]:
    """Return repository path references that do not resolve."""
    problems = []
    candidates = set(PLAYBOOK_RE.findall(text))
    candidates.update(tok for tok in TOKEN_RE.findall(text) if tok.startswith(ANCHORS))
    for ref in candidates:
        if not path_exists(root, ref):
            problems.append(f"missing repository path referenced in docs: {ref}")
    return problems


def main() -> int:
    """Validate references across the instruction/documentation layer."""
    root = repo_root()
    tasks = taskfile_task_names(root)
    problems: list[str] = []
    files = 0
    for path in doc_files(root):
        files += 1
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        for problem in check_go_tasks(text, tasks) + check_paths(root, text):
            problems.append(f"{rel}: {problem}")

    if problems:
        print("stale references in instruction docs:")
        for problem in sorted(set(problems)):
            print(f"  {problem}")
        return 1
    print(f"instruction references resolve: {files} docs, {len(tasks)} known tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
