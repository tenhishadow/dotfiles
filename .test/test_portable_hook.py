"""Black-box tests for the portable Codex hook contract."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "dotfiles/.codex/hooks/portable.py"
HOOKS_CONFIG = ROOT / "dotfiles/.codex/hooks.json"


def _event(command: str, *, tool_name: str = "Bash") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_use_id": "tool-use-test",
            "tool_input": {"command": command},
        }
    )


def _run_hook(
    payload: str, *, optimized: bool = False
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", str(HOOK)))
    return subprocess.run(
        command,
        cwd=ROOT,
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


class PortableHookTest(unittest.TestCase):
    """Exercise the narrow simple-command policy through the JSON interface."""

    def test_manifest_uses_current_pre_tool_use_contract(self) -> None:
        config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
        event = config["hooks"]["PreToolUse"]
        self.assertEqual(1, len(event))
        self.assertEqual("Bash", event[0]["matcher"])
        handlers = event[0]["hooks"]
        self.assertEqual(1, len(handlers))
        self.assertEqual("command", handlers[0]["type"])
        self.assertEqual("python3 ~/.codex/hooks/portable.py", handlers[0]["command"])

    def test_supported_destructive_simple_commands_are_denied(self) -> None:
        commands = (
            "rm -rf /",
            "rm --recursive --force /etc",
            "/bin/rm -r /home",
            "command rm -r /",
            "sudo -n /bin/rm -rf /etc",
            "sudo -u root rm -rf /",
            "env SAFE=yes rm -rf /",
            f"rm -rf {Path.home()}",
            f"rm -rf {ROOT}",
            "git reset --hard HEAD",
            "git -C workspace reset --hard HEAD",
            "git clean -fdx",
            "git clean --force",
            "git clean -f -- -n",
            "git checkout -- README.md",
            "git checkout HEAD README.md",
            "git checkout --ours README.md",
            "git checkout .",
            "git restore README.md",
            "git restore --worktree README.md",
            "git restore -SW README.md",
            "git restore --pathspec-from-file=paths",
            "git switch --discard-changes feature",
            "git switch --force feature",
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                decision = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual("PreToolUse", decision["hookEventName"])
                self.assertEqual("deny", decision["permissionDecision"])
                self.assertTrue(decision["permissionDecisionReason"])
                self.assertNotIn(command, result.stdout)

    def test_supported_narrow_commands_are_allowed(self) -> None:
        commands = (
            "rm -rf /tmp/narrow",
            "rm /",
            "rm --force /etc",
            "git reset -- README.md",
            "git clean -nfdx",
            "git clean --dry-run --force",
            "git checkout feature",
            "git restore --staged README.md",
            "git restore -S README.md",
            "git status --short",
            "command -v rm",
            "command -V rm",
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_unsupported_shell_syntax_and_wrapper_forms_pass_through(self) -> None:
        commands = (
            "printf ok; rm -rf /",
            "printf ok && rm -rf /",
            "printf ok | rm -rf /",
            "printf ok\nrm -rf /",
            "echo $(true; rm -rf /; true)",
            "echo `true; rm -rf /; true`",
            "cat <(true; rm -rf /; true)",
            "echo ${x:-true; rm -rf /; true}",
            "value=$((1 << 2))\nrm -rf /",
            "cat <<'EOF'\nrm -rf /\nEOF",
            "FOO+=x rm -rf /",
            "rm -rf $'/'",
            "rm -rf /*",
            "rm -rf /{*,.*}",
            "rm --recurs /",
            "sudo -nu root rm -rf /",
            "env -iu SAFE rm -rf /",
            "env -S 'rm -rf /'",
            "env --split-string='rm -rf /'",
            "bash -c 'rm -rf /'",
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_non_bash_and_malformed_events_are_ignored(self) -> None:
        cases = (
            _event("rm -rf /", tool_name="Read"),
            json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Bash"}),
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": ["rm", "-rf", "/"]},
                }
            ),
            "{not-json",
            "[]",
            "null",
        )
        for payload in cases:
            with self.subTest(payload=payload):
                result = _run_hook(payload)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_optimized_python_cannot_disable_policy(self) -> None:
        result = _run_hook(_event("rm -rf /"), optimized=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "deny",
            json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
        )


if __name__ == "__main__":
    unittest.main()
