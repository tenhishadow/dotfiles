"""Black-box contracts for portable user dotfiles behavior."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (".test/nvim/terraform/.terraform/terraform.tfstate", 0),
        (".test/nvim/terragrunt/.terraform/plugin-cache/example", 0),
        (".test/nvim/terraform/.terraform/.gitkeep", 1),
        (".test/nvim/terragrunt/.terraform/.gitkeep", 1),
    ],
)
def test_neovim_terraform_runtime_state_is_repository_ignored(
    run_command, repo_root, candidate, expected
):
    result = run_command(
        [
            "git",
            "-c",
            "core.excludesFile=/dev/null",
            "check-ignore",
            "--quiet",
            "--no-index",
            candidate,
        ],
        cwd=repo_root,
    )
    assert result.returncode == expected


@pytest.mark.parametrize(
    ("candidate", "ignored"),
    [
        (name, True)
        for name in (
            "terraform.tfvars",
            "production.auto.tfvars",
            "production.tfvars.json",
            "terraform.tfstate",
            "tfplan",
            "tfplan.binary",
            "production.tfplan",
            "production.tfplan.binary",
            "production.tfbackend",
            "production.tfbackend.json",
            ".terraform.d/credentials.tfrc.json",
        )
    ]
    + [
        (name, False)
        for name in (
            "example.tfvars.example",
            "backend.tfbackend.example",
            "notes-tfplan.md",
            "terraform-plan-notes.md",
        )
    ],
)
def test_global_terraform_ignore_preserves_examples(
    run_command, tmp_path, repo_root, candidate, ignored
):
    run_command(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    result = run_command(
        [
            "git",
            "-c",
            f"core.excludesFile={repo_root / 'dotfiles/.gitignore'}",
            "check-ignore",
            "--quiet",
            "--no-index",
            candidate,
        ],
        cwd=tmp_path,
    )
    assert result.returncode == (0 if ignored else 1)


def test_completion_generators_are_lazy_and_work_on_first_use(
    tmp_path, repo_root
):
    commands = (
        "checkov",
        "docker",
        "gh",
        "go-task",
        "helm",
        "kubectl",
        "register-python-argcomplete",
        "tput",
    )
    temporary_path = tmp_path
    binary_directory = temporary_path / "bin"
    binary_directory.mkdir()
    trace_path = temporary_path / "completion-trace"
    stub = (
        "#!/bin/sh\n"
        'printf \'%s\\n\' "${0##*/}" >>"$DOTFILES_COMPLETION_TRACE"\n'
    )
    for command in commands:
        command_path = binary_directory / command
        command_path.write_text(stub, encoding="utf-8")
        command_path.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "DOTFILES_COMPLETION_TRACE": str(trace_path),
            "HOME": str(temporary_path),
            "PATH": f"{binary_directory}:{environment['PATH']}",
            "TERM": "xterm",
        }
    )
    subprocess.run(
        [
            "bash",
            "--noprofile",
            "--rcfile",
            str(repo_root / "dotfiles/.bashrc"),
            "-i",
            "-c",
            "exit",
        ],
        check=True,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
    )

    assert not trace_path.exists(), (
        "interactive startup eagerly invoked a completion generator"
    )

    go_task_path = binary_directory / "go-task"
    go_task_path.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' generator >>\"$DOTFILES_COMPLETION_TRACE\"\n"
        "printf '%s\\n' '_task() { printf \"%s\\n\" completion "
        '>>"$DOTFILES_COMPLETION_TRACE"; }\'\n',
        encoding="utf-8",
    )
    subprocess.run(
        [
            "bash",
            "--noprofile",
            "--rcfile",
            str(repo_root / "dotfiles/.bashrc"),
            "-i",
            "-c",
            "_dotfiles_load_go_task_completion; exit",
        ],
        check=True,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
    )
    assert trace_path.read_text(encoding="utf-8").splitlines() == [
        "generator",
        "completion",
    ]


def test_dumb_terminal_does_not_receive_less_color_sequences(
    run_command, tmp_path, repo_root
):
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("LESS_TERMCAP_"):
            environment.pop(name)
    environment.update({"HOME": str(tmp_path), "TERM": "dumb"})

    result = run_command(
        [
            "bash",
            "--noprofile",
            "--rcfile",
            str(repo_root / "dotfiles/.bashrc"),
            "-i",
            "-c",
            'printf \'%s\\n\' "$LESS" "${LESS_TERMCAP_md-unset}"',
        ],
        check=True,
        env=environment,
        timeout=15,
    )
    assert result.stdout.splitlines()[-2:] == ["-R", "unset"]


def test_mplayer_baseline_uses_auto_selection(repo_root: Path):
    config = (repo_root / "dotfiles/.mplayer/config").read_text(
        encoding="utf-8"
    )
    assert not re.search("(?im)^\\s*v[oc]\\s*=", config)


@pytest.mark.skipif(
    not shutil.which("mplayer"), reason="Optional local MPlayer parser probe"
)
@pytest.mark.parametrize(
    "invalid", [False, True], ids=["baseline", "invalid-option"]
)
def test_local_mplayer_probe_reads_the_isolated_config(
    run_command, tmp_path, repo_root, invalid
):
    directory = tmp_path / ".mplayer"
    directory.mkdir()
    config = (repo_root / "dotfiles/.mplayer/config").read_text()
    if invalid:
        config += "\nnot_a_real_mplayer_setting=yes\n"
    (directory / "config").write_text(config, encoding="utf-8")
    result = run_command(
        ["mplayer", "-vo", "help"], env={**os.environ, "HOME": str(tmp_path)}
    )
    output = result.stdout + result.stderr
    assert "Available video output drivers:" in output
    assert "Failed to read" not in output
    parser_error = bool(re.search(r"(?i)(unknown option|at line \d+)", output))
    assert parser_error is invalid, output
