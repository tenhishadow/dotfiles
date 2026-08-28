#!/usr/bin/env python3
"""Block a narrow set of unmistakably destructive simple commands.

This dependency-free hook is a convenience guardrail, not a shell parser or a
security boundary. It inspects one simple command only. Shell expansions,
redirections, compound commands, and other complex syntax are passed through.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import sys

UNSUPPORTED_SHELL = re.compile(r"[\n\r;&|<>(){}$`\\*?\[\]#~]")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
BROAD_RM_TARGETS = {
    ".",
    "..",
    "/",
    "//",
    "/boot",
    "/etc",
    "/home",
    "/opt",
    "/root",
    "/srv",
    "/usr",
    "/var",
}
SUDO_FLAGS = {"-E", "-H", "-K", "-S", "-b", "-k", "-n", "--non-interactive"}
SUDO_OPTIONS_WITH_VALUES = {
    "-C",
    "-D",
    "-g",
    "-h",
    "-p",
    "-R",
    "-T",
    "-u",
    "--chdir",
    "--group",
    "--host",
    "--user",
}


def _simple_words(command: str) -> list[str] | None:
    """Return argv for one expansion-free simple command."""
    if not command.strip() or UNSUPPORTED_SHELL.search(command):
        return None
    try:
        words = shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None
    return words or None


def _skip_explicit_options(
    words: list[str], index: int, flags: set[str], values: set[str]
) -> int | None:
    """Skip only explicitly supported, unclustered wrapper options."""
    while index < len(words):
        word = words[index]
        if word == "--":
            return index + 1
        option, separator, _value = word.partition("=")
        if word in flags:
            index += 1
        elif option in values:
            if separator:
                index += 1
            elif index + 1 < len(words):
                index += 2
            else:
                return None
        elif word.startswith("-"):
            return None
        else:
            break
    return index


def _unwrap(words: list[str]) -> list[str] | None:
    """Remove a small set of common wrappers with explicit option syntax."""
    index = 0
    while index < len(words):
        executable = os.path.basename(words[index])
        if executable == "command":
            index += 1
            if index < len(words) and words[index] in {"-v", "-V"}:
                return None
            index = _skip_explicit_options(words, index, {"-p"}, set())
        elif executable == "sudo":
            index = _skip_explicit_options(
                words, index + 1, SUDO_FLAGS, SUDO_OPTIONS_WITH_VALUES
            )
        elif executable == "env":
            index = _skip_explicit_options(words, index + 1, {"-i"}, {"-u"})
            if index is not None:
                while index < len(words) and ASSIGNMENT.match(words[index]):
                    index += 1
        else:
            return words[index:]
        if index is None:
            return None
    return None


def _broad_rm_targets() -> set[str]:
    """Return literal broad targets for this hook invocation."""
    targets = set(BROAD_RM_TARGETS)
    home = posixpath.normpath(os.path.expanduser("~"))
    try:
        cwd = posixpath.normpath(os.getcwd())
    except OSError:
        cwd = ""
    for root in (home, cwd):
        if root and root != ".":
            targets.add(root)
    if home and home != ".":
        targets.update(
            posixpath.join(home, child)
            for child in (".cache", ".config", ".gnupg", ".local", ".ssh")
        )
    return targets


def _rm_is_broad(arguments: list[str]) -> bool:
    recursive = False
    targets: list[str] = []
    options_done = False
    for argument in arguments:
        if not options_done and argument == "--":
            options_done = True
        elif not options_done and argument == "--recursive":
            recursive = True
        elif not options_done and argument.startswith("--"):
            continue
        elif not options_done and argument.startswith("-"):
            recursive = recursive or "r" in argument[1:] or "R" in argument[1:]
        elif argument:
            targets.append(posixpath.normpath(argument))
    return recursive and any(target in _broad_rm_targets() for target in targets)


def _git_arguments(words: list[str]) -> list[str] | None:
    """Return argv after a small supported set of Git global options."""
    flags = {"--no-pager"}
    values = {"-C", "-c", "--git-dir", "--work-tree"}
    index = _skip_explicit_options(words, 1, flags, values)
    return None if index is None else words[index:]


def _git_clean_is_destructive(options: list[str]) -> bool:
    forced = False
    dry_run = False
    for option in options:
        if option == "--":
            break
        if option == "--force":
            forced = True
        elif option == "--dry-run":
            dry_run = True
        elif option.startswith("--"):
            if option not in {"--directories", "--ignored", "--quiet"}:
                return False
        elif option.startswith("-"):
            flags = option[1:]
            if not flags or not set(flags) <= set("dfinqxX"):
                return False
            forced = forced or "f" in flags
            dry_run = dry_run or "n" in flags
    return forced and not dry_run


def _git_checkout_is_destructive(options: list[str]) -> bool:
    operands: list[str] = []
    path_mode = False
    for index, option in enumerate(options):
        if option == "--":
            return index + 1 < len(options)
        if option in {"--force", "-f"}:
            return True
        if option in {"--ours", "--theirs"}:
            path_mode = True
        elif option == "--quiet" or (
            option.startswith("-") and set(option[1:]) <= {"f", "q"}
        ):
            if "f" in option[1:]:
                return True
        elif option.startswith("-"):
            return False
        else:
            operands.append(option)
    explicit_relative = any(
        operand in {".", ".."} or operand.startswith(("./", "../"))
        for operand in operands
    )
    return explicit_relative or len(operands) > 1 or (path_mode and bool(operands))


def _git_restore_is_destructive(options: list[str]) -> bool:
    staged = False
    worktree = False
    paths: list[str] = []
    for index, option in enumerate(options):
        if option == "--":
            paths.extend(options[index + 1 :])
            break
        if option == "--pathspec-from-file" or option.startswith(
            "--pathspec-from-file="
        ):
            return True
        if option in {"--staged", "-S"}:
            staged = True
        elif option in {"--worktree", "-W"}:
            worktree = True
        elif option == "-SW":
            staged = worktree = True
        elif option.startswith("-"):
            return False
        else:
            paths.append(option)
    return bool(paths) and (worktree or not staged)


def _git_is_destructive(words: list[str]) -> bool:
    arguments = _git_arguments(words)
    if not arguments:
        return False
    subcommand, *options = arguments
    if subcommand == "reset":
        return "--hard" in options
    if subcommand == "switch":
        force_options = {"--discard-changes", "--force", "-f"}
        return any(option in force_options for option in options)
    checks = {
        "clean": _git_clean_is_destructive,
        "checkout": _git_checkout_is_destructive,
        "restore": _git_restore_is_destructive,
    }
    check = checks.get(subcommand)
    return bool(check and check(options))


def policy_reason(command: str) -> str | None:
    """Return a denial reason for a supported destructive simple command."""
    command_words = _simple_words(command)
    if command_words is None:
        return None
    words = _unwrap(command_words)
    if not words:
        return None
    executable = os.path.basename(words[0])
    if executable == "rm" and _rm_is_broad(words[1:]):
        return "Broad recursive removal blocked by the portable Codex guard."
    if executable == "git" and _git_is_destructive(words):
        return "Destructive Git command blocked by the portable Codex guard."
    return None


def _deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload, separators=(",", ":")))


def main() -> None:
    """Evaluate one Codex hook event from standard input."""
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError, OSError:
        return
    if not isinstance(event, dict):
        return
    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        return
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    command = tool_input.get("command")
    if not isinstance(command, str):
        return
    reason = policy_reason(command)
    if reason:
        _deny(reason)


if __name__ == "__main__":
    main()
