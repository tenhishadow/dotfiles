"""Black-box tests for the portable Codex hook JSON contract."""

import json
import os
import sys
from pathlib import Path

import pytest


def _event(command: str, *, tool_name: str = "Bash") -> str:
    """Serialize a synthetic native hook event."""
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_use_id": "tool-use-test",
            "tool_input": {"command": command},
        }
    )


@pytest.fixture(name="run_hook")
def fixture_run_hook(run_command, repo_root: Path, tmp_path: Path):
    """Invoke the hook in isolation; commands are input, never executed."""

    def run(payload: str, *, optimized: bool = False):
        command = [
            sys.executable,
            *(["-O"] if optimized else []),
            "-I",
            str(repo_root / "dotfiles/.codex/hooks/portable.py"),
        ]
        return run_command(
            command,
            cwd=tmp_path,
            input=payload,
            timeout=5,
            env={
                "PATH": os.environ.get("PATH", os.defpath),
                "HOME": str(tmp_path / "home"),
            },
        )

    return run


def test_manifest_uses_current_pre_tool_use_contract(repo_root: Path):
    config = json.loads((repo_root / "dotfiles/.codex/hooks.json").read_text())
    event = config["hooks"]["PreToolUse"]
    assert len(event) == 1
    assert event[0]["matcher"] == "Bash"
    handlers = event[0]["hooks"]
    assert len(handlers) == 1
    assert handlers[0]["type"] == "command"
    assert handlers[0]["command"] == "python3 ~/.codex/hooks/portable.py"


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "rm --recursive --force /etc",
        "/bin/rm -r /home",
        "command rm -r /",
        "sudo -n /bin/rm -rf /etc",
        "sudo -u root rm -rf /",
        "env SAFE=yes rm -rf /",
        "rm -rf @HOME@",
        "rm -rf @CWD@",
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
    ],
)
def test_supported_destructive_simple_commands_are_denied(
    command, run_hook, tmp_path
):
    command = command.replace("@HOME@", str(tmp_path / "home")).replace(
        "@CWD@", str(tmp_path)
    )
    result = run_hook(_event(command))
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"]
    assert command not in result.stdout


@pytest.mark.parametrize(
    "command",
    [
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
    ],
)
def test_supported_narrow_commands_are_allowed(command, run_hook):
    result = run_hook(_event(command))
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "command",
    [
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
    ],
)
def test_unsupported_shell_syntax_and_wrapper_forms_pass_through(
    command, run_hook
):
    result = run_hook(_event(command))
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "payload",
    [
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
    ],
)
def test_non_bash_and_malformed_events_are_ignored(payload, run_hook):
    result = run_hook(payload)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_optimized_python_cannot_disable_policy(run_hook):
    result = run_hook(_event("rm -rf /"), optimized=True)
    assert result.returncode == 0, result.stderr
    assert (
        json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
        == "deny"
    )
