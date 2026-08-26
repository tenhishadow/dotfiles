"""Black-box tests for the portable Codex hook contract."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "dotfiles/.codex/hooks/portable.py"


def _event(command: str, *, tool_name: str = "Bash") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
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
    """Exercise policy decisions through the hook's JSON interface."""

    def test_sensitive_and_destructive_commands_are_denied(self) -> None:
        token = "literal-" + "credential"
        commands = (
            "rm -rf /",
            "git reset --hard HEAD",
            "git clean -fdx",
            "kubectl logs pod",
            "kubectl logs pod --tail=-1",
            "docker logs container",
            "journalctl -u unit",
            f"API_TOKEN={token} command",
            "cat ~/.ssh/id_ed25519",
            "source .test/system/local.env",
            "cat ~/.kube/config",
            'printf "%s" "$KUBECONFIG"',
            "kubectl --kubeconfig=/tmp/cluster.yaml get pods",
            "cat ~/.gnupg/private-keys-v1.d/key",
            'cat "$GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE"',
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                output = json.loads(result.stdout)
                decision = output["hookSpecificOutput"]
                self.assertEqual("PreToolUse", decision["hookEventName"])
                self.assertEqual("deny", decision["permissionDecision"])
                self.assertTrue(decision["permissionDecisionReason"])
                self.assertNotIn(command, result.stdout)

    def test_narrow_and_public_commands_are_allowed(self) -> None:
        commands = (
            "rm -rf /tmp/narrow",
            "kubectl logs pod --tail=100",
            "journalctl -u unit | head -n 50",
            "API_TOKEN=$TOKEN command",
            "cat dotfiles/.ssh/config",
            "cat ~/.ssh/config.d/work",
            "cat ~/.ssh/id_ed25519.pub",
            "cat .test/system/local.env.example",
            "cat dotfiles/.gnupg/gpg.conf",
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
            "{not-json",
            "[]",
            "null",
            '"text"',
            "42",
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
