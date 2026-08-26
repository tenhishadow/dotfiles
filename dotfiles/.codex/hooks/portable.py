#!/usr/bin/env python3
"""Small, deterministic Codex lifecycle guardrails."""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?(?:key|token)|access[_-]?token|auth[_-]?token|token|"
    r"password|passwd|secret)"
    r"\b\s*(?:=|:)\s*([^\s;&|]+)"
)
SECRET_FLAG = re.compile(
    r"(?i)--(?:api[_-]?(?:key|token)|access[_-]?token|auth[_-]?token|token|"
    r"password|secret)"
    r"(?:=|\s+)\s*([^\s;&|]+)"
)
BEARER = re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+([^\s'\"]+)")
URL_CREDENTIALS = re.compile(r"(?i)\bhttps?://[^\s/:]+:[^\s/@]+@")
SENSITIVE_PATH_REFERENCE = re.compile(
    r"(?:\$(?:KUBECONFIG\b|\{KUBECONFIG\b|"
    r"GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE\b|"
    r"\{GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE\b)|"
    r"(?<![A-Za-z0-9_])(?:KUBECONFIG|"
    r"GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE)\s*=|--kubeconfig(?:=|\s))"
)
SHELL_WORD = re.compile(r"""[^\s;&|<>"']+""")
SAFE_VALUE_PREFIXES = (
    "$",
    "${",
    "<",
    "your_",
    "redacted",
    "example",
    "dummy",
    "test",
    "changeme",
)


def _literal_secret(value: str) -> bool:
    candidate = value.strip("'\"").lower()
    return len(candidate) >= 8 and not candidate.startswith(SAFE_VALUE_PREFIXES)


def _dangerous_rm(command: str) -> bool:
    pattern = re.compile(r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+([^;&|\n]+)")
    for match in pattern.finditer(command):
        try:
            words = shlex.split(match.group(1))
        except ValueError:
            continue
        recursive = False
        force = False
        targets: list[str] = []
        parse_options = True
        for word in words:
            if parse_options and word == "--":
                parse_options = False
            elif parse_options and word.startswith("--"):
                recursive |= word == "--recursive"
                force |= word == "--force"
            elif parse_options and word.startswith("-"):
                recursive |= "r" in word.lower()
                force |= "f" in word.lower()
            else:
                targets.append(word)
        if not (recursive and force):
            continue
        home = str(Path.home())
        broad = {
            "/",
            "/*",
            "/.*",
            ".",
            "..",
            "./*",
            "../*",
            "~",
            "~/",
            "~/*",
            "$HOME",
            "$HOME/",
            "$HOME/*",
            "${HOME}",
            "${HOME}/",
            "${HOME}/*",
            home,
            f"{home}/",
            f"{home}/*",
        }
        if any(target in broad for target in targets):
            return True
    return False


def _dangerous_git(command: str) -> bool:
    if re.search(r"\bgit(?:\s+-C\s+\S+)?\s+reset\s+--hard\b", command):
        return True
    for match in re.finditer(r"\bgit(?:\s+-C\s+\S+)?\s+clean\s+([^;&|\n]+)", command):
        try:
            words = shlex.split(match.group(1))
        except ValueError:
            continue
        flags = "".join(word[1:] for word in words if word.startswith("-"))
        if "f" in flags and ("d" in flags or "x" in flags):
            return True
    return False


def _contains_literal_secret(command: str) -> bool:
    if URL_CREDENTIALS.search(command):
        return True
    for pattern in (SECRET_ASSIGNMENT, SECRET_FLAG, BEARER):
        if any(_literal_secret(match.group(1)) for match in pattern.finditer(command)):
            return True
    return False


def _contains_sensitive_path(command: str) -> bool:
    if SENSITIVE_PATH_REFERENCE.search(command):
        return True
    for word in SHELL_WORD.findall(command):
        segments = [segment.strip("()[]{},:") for segment in word.split("/")]
        candidates = [segment.rsplit("=", 1)[-1] for segment in segments]
        if ".ssh" in candidates:
            remainder = candidates[candidates.index(".ssh") + 1 :]
            public_config = remainder == ["config"] or (
                remainder and remainder[0] == "config.d" and ".." not in remainder
            )
            public_key = (
                remainder and remainder[-1].endswith(".pub") and ".." not in remainder
            )
            if not (public_config or public_key):
                return True
            continue
        if ".gnupg" in candidates:
            remainder = candidates[candidates.index(".gnupg") + 1 :]
            if "private-keys-v1.d" in remainder:
                return True
        for candidate in candidates:
            if candidate == ".kube":
                return True
            if candidate.endswith(".env.example"):
                continue
            if (
                candidate == ".env"
                or candidate.startswith(".env.")
                or candidate.endswith(".env")
            ):
                return True
    return False


def _bounded_output(command: str) -> bool:
    return bool(
        re.search(
            r"(?:\|\s*(?:head|tail)\b|\|\s*sed\s+-n\b|"
            r"\|\s*rg\b[^|;&\n]*\s(?:-m|--max-count)\b|"
            r"(?:^|\s)(?:>|>>)\s*\S+)",
            command,
        )
    )


def _unbounded_logs(command: str) -> bool:
    bounded_pipe = _bounded_output(command)
    if re.search(r"--tail(?:=|\s+)-1(?:\s|$)", command) and not bounded_pipe:
        return True
    checks = (
        (
            re.compile(r"\bkubectl\b[^;&|\n]*\blogs\b"),
            re.compile(r"--(?:tail|since|since-time|limit-bytes)(?:=|\s)"),
        ),
        (
            re.compile(r"\b(?:docker|podman)\s+logs\b"),
            re.compile(r"--(?:tail|since|until)(?:=|\s)"),
        ),
        (
            re.compile(r"\bjournalctl\b"),
            re.compile(
                r"(?:^|\s)(?:-n\s*\d+|--lines(?:=|\s)|--since(?:=|\s)|--until(?:=|\s))"
            ),
        ),
    )
    for command_pattern, bound_pattern in checks:
        if not command_pattern.search(command):
            continue
        follows = bool(re.search(r"(?:^|\s)(?:-f|--follow)(?:\s|$)", command))
        if follows and not bounded_pipe:
            return True
        if not bounded_pipe and not bound_pattern.search(command):
            return True
    return False


def policy_reason(command: str) -> str | None:
    """Return a generic denial reason without echoing sensitive input."""
    if _dangerous_rm(command) or _dangerous_git(command):
        return "Broad destructive command blocked by the portable Codex policy."
    if _contains_literal_secret(command):
        return (
            "Credential-shaped literal blocked; use a protected file or "
            "environment reference."
        )
    if _contains_sensitive_path(command):
        return "Sensitive local path blocked by the portable Codex policy."
    if _unbounded_logs(command):
        return "Unbounded log command blocked; add a line, time, or output limit."
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
    event_name = event.get("hook_event_name")
    if event_name != "PreToolUse" or event.get("tool_name") != "Bash":
        return
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    command = tool_input.get("command", tool_input.get("cmd"))
    if not isinstance(command, str):
        return
    reason = policy_reason(command)
    if reason:
        _deny(reason)


if __name__ == "__main__":
    main()
