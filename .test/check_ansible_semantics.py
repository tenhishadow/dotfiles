#!/usr/bin/env python3
"""Enforce the repo Ansible naming and notify/handler rules structurally.

ansible-lint already covers FQCN, var-naming, modes, and the generic name
rules. It does not express two repo-specific contracts, so this check makes
them mechanical instead of prose:

  1. Every play, task, and handler name follows ``<Domain> | <Verb> <object>``:
     a single `` | `` separator, a capitalized domain, and a capitalized verb
     followed by a non-empty object. The verb and domain vocabularies in
     AGENTS.md are illustrative ("for example"), so only the *shape* is
     enforced, never a closed word list.
  2. Every literal ``notify`` value resolves to a handler name that exists in
     the same role (the exact-match rule between ``notify`` and handler names).

It walks the YAML structurally (plays, pre_tasks/tasks/post_tasks/handlers,
and nested block/rescue/always) so ``name:`` keys that are module parameters
or loop-item data are never mistaken for task names. Run via the uv
environment so PyYAML is available:

    uv run python .test/check_ansible_semantics.py
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import yaml

# A play/task/handler name: "<Domain> | <Verb> <object>".
# Domain starts with a letter, may carry product casing and spaces.
# After the single " | " separator: a capitalized verb and a non-empty object.
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ]*\| [A-Z][A-Za-z0-9]*\s+\S.*$")
SEPARATOR = " | "

BLOCK_KEYS = ("block", "rescue", "always")
PLAY_TASK_KEYS = ("pre_tasks", "tasks", "post_tasks", "handlers")


def repo_root() -> Path:
    """Return the repository root (parent of the .test directory)."""
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path):
    """Load a YAML document, returning [] for an empty file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if data is not None else []


def role_of(path: Path, root: Path) -> str | None:
    """Return the role name for a path under roles/<role>/, else None."""
    rel = path.relative_to(root).parts
    if len(rel) >= 2 and rel[0] == "roles":
        return rel[1]
    return None


def iter_tasks(tasks):
    """Yield every task dict in a task list, descending block/rescue/always."""
    if not isinstance(tasks, list):
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        yield task
        for key in BLOCK_KEYS:
            if key in task:
                yield from iter_tasks(task[key])


def iter_named_units(path: Path):
    """Yield (kind, name) for every play/task/handler defined in a file.

    Playbooks hold plays whose task keys are walked; role tasks/handlers files
    hold a bare task list.
    """
    doc = load_yaml(path)
    is_playbook = path.name.startswith("playbook_")
    if is_playbook:
        for play in doc if isinstance(doc, list) else []:
            if not isinstance(play, dict):
                continue
            yield "play", play.get("name")
            for key in PLAY_TASK_KEYS:
                for task in iter_tasks(play.get(key)):
                    kind = "handler" if key == "handlers" else "task"
                    yield kind, task.get("name")
    else:
        kind = "handler" if path.parent.name == "handlers" else "task"
        for task in iter_tasks(doc):
            yield kind, task.get("name")


def collect_handler_names(root: Path) -> dict[str, set[str]]:
    """Map role name -> set of handler names defined in that role."""
    handlers: dict[str, set[str]] = {}
    for path in sorted(root.glob("roles/*/handlers/*.yml")):
        role = role_of(path, root)
        for task in iter_tasks(load_yaml(path)):
            name = task.get("name")
            if role and isinstance(name, str):
                handlers.setdefault(role, set()).add(name)
    return handlers


def collect_notifies(path: Path):
    """Yield literal notify handler names referenced by tasks in a file."""
    for task in iter_tasks(load_yaml(path)):
        notify = task.get("notify")
        values = notify if isinstance(notify, list) else [notify]
        for value in values:
            if isinstance(value, str) and "{{" not in value:
                yield value


def check_names(root: Path, files: list[Path]) -> list[str]:
    """Return formatting violations for play/task/handler names."""
    problems = []
    for path in files:
        rel = path.relative_to(root)
        for kind, name in iter_named_units(path):
            if name is None:
                continue  # ansible-lint owns "name missing"
            if not isinstance(name, str) or not NAME_RE.match(name):
                problems.append(f"{rel}: {kind} name not '<Domain> | <Verb> <object>': {name!r}")
            elif name.count(SEPARATOR) != 1:
                problems.append(f"{rel}: {kind} name needs exactly one ' | ' separator: {name!r}")
    return problems


def check_notify(root: Path, files: list[Path]) -> list[str]:
    """Return notify values that do not match a handler name in the role."""
    handlers = collect_handler_names(root)
    known = set().union(*handlers.values()) if handlers else set()
    problems = []
    for path in files:
        rel = path.relative_to(root)
        role = role_of(path, root)
        scope = handlers.get(role, set()) if role else known
        for value in collect_notifies(path):
            if value not in scope and value not in known:
                problems.append(f"{rel}: notify '{value}' has no matching handler name")
    return problems


def main() -> int:
    """Run both Ansible semantic checks and report any violations."""
    root = repo_root()
    files = [
        Path(p)
        for p in sorted(
            glob.glob(str(root / "roles/*/tasks/*.yml"))
            + glob.glob(str(root / "roles/*/handlers/*.yml"))
            + glob.glob(str(root / "playbook_*.yml"))
        )
    ]
    problems = check_names(root, files) + check_notify(root, files)
    if problems:
        print("ansible semantic violations:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"ansible semantics consistent: {len(files)} files, names and notify/handlers match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
