"""Exercise Task command boundaries with isolated recorder executables."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

TASK_BINARY = shutil.which("go-task") or shutil.which("task")
RECORDER = """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
record = {
    "tool": name,
    "args": sys.argv[1:],
    "cwd": os.getcwd(),
    "env": {key: os.environ.get(key) for key in (
        "HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
        "XDG_CACHE_HOME", "GOENV", "NVIM_USE_MASON", "NVIM_TS_INSTALL",
        "NVIM_APPNAME", "NVIM_DOTFILES_DISABLE_PLUGINS", "SKIP"
    )},
}
with open(os.environ["TASK_TEST_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(record) + "\\n")
if name == "git" and "ls-files" in sys.argv:
    sys.stdout.write("tracked.md\\0draft note.md\\0")
"""


@pytest.fixture(name="task_repo")
def _task_repo(tmp_path, repo_root, monkeypatch):
    assert TASK_BINARY, "Install Task to run task boundary tests."
    root = tmp_path / "checkout with spaces"
    root.mkdir()
    shutil.copyfile(repo_root / "Taskfile.yml", root / "Taskfile.yml")
    binary_directory = root / "bin"
    binary_directory.mkdir()
    for name in (
        "uv",
        "git",
        "sudo",
        "docker",
        "nvim",
        "node",
        "npx",
        "npm",
        "go",
        "renovate-config-validator",
    ):
        executable = binary_directory / name
        executable.write_text(RECORDER, encoding="utf-8")
        executable.chmod(0o755)
    for name in (
        "DOTFILES_ENV_FILE",
        "DOTFILES_PYPI_INDEX_URL",
        "DOTFILES_TEST_PYPI_INDEX_URL",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in {
        "PATH": f"{binary_directory}{os.pathsep}{os.environ['PATH']}",
        "TASK_TEST_LOG": str(root / "calls.jsonl"),
        "UV_NO_SYNC": "false",
        "XDG_CONFIG_HOME": "/outside/config",
        "XDG_DATA_HOME": "/outside/data",
        "XDG_STATE_HOME": "/outside/state",
        "XDG_CACHE_HOME": "/outside/cache",
        "GITHUB_TOKEN": "task-test-placeholder",
        "PINACT_GITHUB_TOKEN": "task-test-placeholder",
    }.items():
        monkeypatch.setenv(name, value)
    scratch = root / "scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
    return root


def _run(root, *arguments, subdirectory=False):
    (root / "calls.jsonl").unlink(missing_ok=True)
    workdir = root / "nested" if subdirectory else root
    workdir.mkdir(exist_ok=True)
    return subprocess.run(
        (TASK_BINARY, "--silent", *arguments),
        cwd=workdir,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _calls(root, *arguments, subdirectory=False):
    completed = _run(root, *arguments, subdirectory=subdirectory)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return _read_calls(root)


def _read_calls(root):
    return [
        json.loads(line)
        for line in (root / "calls.jsonl").read_text().splitlines()
    ]


def _nvim_config(root):
    config = root / "dotfiles/.config/nvim"
    (config / "lua/plugins").mkdir(parents=True)
    (config / "init.lua").touch()
    lock = config / "lazy-lock.json"
    lock.write_text('{"original": true}\n', encoding="utf-8")
    return lock


def test_default_applies_only_user_dotfiles_from_checkout_root(task_repo):
    calls = _calls(task_repo, "--", "--tags", "links", subdirectory=True)
    playbooks = [call for call in calls if "ansible-playbook" in call["args"]]
    assert [call["args"] for call in playbooks] == [
        ["run", "ansible-playbook", "playbook_install.yml", "--tags", "links"]
    ]
    assert all(call["cwd"] == str(task_repo) for call in calls)
    assert not any(call["tool"] == "sudo" for call in calls)


def test_all_preserves_order_and_sets_up_dependencies_once(task_repo):
    calls = _calls(task_repo, "all")
    sync = [call for call in calls if call["args"][0] == "sync"]
    assert len(sync) == 1
    assert "--locked" in sync[0]["args"]
    assert sum("ansible-galaxy" in call["args"] for call in calls) == 1
    assert [
        call["args"][2] for call in calls if "ansible-playbook" in call["args"]
    ] == [
        "playbook_install.yml",
        "playbook_system.yml",
        "playbook_browser_policies.yml",
    ]


@pytest.mark.parametrize(
    "task", ["dotfiles:check", "system:check", "browser-policies:check"]
)
def test_check_tasks_preserve_flags_and_quoted_cli_arguments(task_repo, task):
    calls = _calls(
        task_repo, task, "--", "--extra-vars", '{"value":"two words"}'
    )
    command = next(
        call["args"] for call in calls if "ansible-playbook" in call["args"]
    )
    assert "--check" in command
    assert "--diff" in command
    assert command[command.index("--extra-vars") + 1] == '{"value":"two words"}'


def test_python_sync_respects_the_container_mirror_environment(
    task_repo, monkeypatch
):
    monkeypatch.setenv("UV_NO_SYNC", "true")
    calls = _calls(task_repo, "all")
    assert not any(call["args"][0] == "sync" for call in calls)


def _uv_calls(calls, *subcommand):
    """Return uv invocations whose subcommand matches, ignoring global flags."""
    matched = []
    for call in calls:
        if call["tool"] != "uv":
            continue
        args = call["args"]
        start = 0
        while start < len(args) and args[start].startswith("-"):
            start += 1
        if tuple(args[start : start + len(subcommand)]) == subcommand:
            matched.append(args)
    return matched


def test_python_sync_without_an_index_keeps_the_locked_project_sync(task_repo):
    calls = _calls(task_repo, "default")
    assert _uv_calls(calls, "sync")
    assert not _uv_calls(calls, "pip", "sync")


@pytest.mark.parametrize("environment_path", [None, "relative", "absolute"])
def test_python_sync_installs_into_the_project_environment_it_creates(
    task_repo, monkeypatch, environment_path
):
    (task_repo / "local.env").write_text(
        "DOTFILES_PYPI_INDEX_URL=https://packages.example/simple/\n",
        encoding="utf-8",
    )
    # An activated unrelated environment must not become the sync target:
    # `uv pip sync` resolves to $VIRTUAL_ENV when no --python is given, which
    # would uninstall that environment's packages and leave .venv empty.
    monkeypatch.setenv("VIRTUAL_ENV", "/outside/foreign-venv")
    project_environment = ".venv"
    if environment_path is not None:
        project_environment = "custom environment"
        if environment_path == "absolute":
            project_environment = str(
                task_repo / "scratch" / project_environment
            )
        monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", project_environment)
    calls = _calls(task_repo, "default")

    assert not _uv_calls(calls, "sync"), (
        "the locked project sync must be skipped"
    )
    venv = _uv_calls(calls, "venv")[0]
    assert venv[-1] == project_environment

    sync = _uv_calls(calls, "pip", "sync")[0]
    assert sync[sync.index("--python") + 1] == (
        f"{project_environment}/bin/python"
    )
    assert (
        sync[sync.index("--default-index") + 1]
        == "https://packages.example/simple/"
    )
    assert "--require-hashes" in sync


def test_python_sync_reads_an_absolute_environment_file(task_repo, monkeypatch):
    # `. "./${candidate}"` turns an absolute path into a relative one, so the
    # file cannot be sourced and dependency setup fails.
    env_file = task_repo / "scratch/elsewhere.env"
    env_file.write_text(
        "DOTFILES_PYPI_INDEX_URL=https://absolute.example/simple/\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DOTFILES_ENV_FILE", str(env_file))
    calls = _calls(task_repo, "default")

    sync = _uv_calls(calls, "pip", "sync")[0]
    assert (
        sync[sync.index("--default-index") + 1]
        == "https://absolute.example/simple/"
    )


@pytest.mark.parametrize("failed_command", ["venv", "export", "pip"])
def test_mirror_setup_failure_prevents_install_and_public_fallback(
    task_repo, failed_command
):
    (task_repo / "local.env").write_text(
        "DOTFILES_PYPI_INDEX_URL=https://packages.example/simple/\n",
        encoding="utf-8",
    )
    (task_repo / "bin/uv").write_text(
        RECORDER
        + f"\nif {failed_command!r} in sys.argv:\n    raise SystemExit(9)\n",
        encoding="utf-8",
    )
    completed = _run(task_repo, "default")
    assert completed.returncode != 0
    calls = _read_calls(task_repo)
    assert not _uv_calls(calls, "sync")
    assert not _uv_calls(calls, "run")


def test_superlinter_quotes_mounts_and_reuses_the_latest_image_runner(
    task_repo,
):
    envfile = task_repo / "local.env"
    envfile.write_text("TEST_MIRROR=private\n", encoding="utf-8")
    calls = _calls(task_repo, "superlinter:latest")
    command = next(call["args"] for call in calls if call["args"][0] == "run")
    assert f"{task_repo}:/tmp/lint" in command
    assert f"{task_repo}/local.env.example:/tmp/lint/local.env:ro" in command
    assert command[-1] == "ghcr.io/super-linter/super-linter:slim-latest"


def test_neovim_compat_ignores_exported_user_xdg_paths(task_repo):
    _nvim_config(task_repo)
    calls = _calls(task_repo, "test:nvim:compat", subdirectory=True)
    environment = next(call["env"] for call in calls if call["tool"] == "nvim")
    for variable, suffix in (
        ("HOME", ".home"),
        ("XDG_CONFIG_HOME", ".config"),
        ("XDG_DATA_HOME", ".data"),
        ("XDG_STATE_HOME", ".state"),
        ("XDG_CACHE_HOME", ".cache"),
    ):
        assert environment[variable] == str(task_repo / ".test/nvim" / suffix)
    assert environment["NVIM_USE_MASON"] == "off"


def test_failed_neovim_upgrade_cannot_publish_a_partial_lock(task_repo):
    lock = _nvim_config(task_repo)
    (task_repo / "bin/nvim").write_text(
        RECORDER
        + '\n(Path(os.environ["XDG_CONFIG_HOME"]) / "nvim/lazy-lock.json")'
        '.write_text("partial update\\n", encoding="utf-8")\n'
        "raise SystemExit(9)\n",
        encoding="utf-8",
    )
    completed = _run(task_repo, "deps-upgrade:nvim")
    assert completed.returncode != 0
    assert "exit status 9" in completed.stderr
    assert lock.read_text() == '{"original": true}\n'
    assert not list((task_repo / "scratch").iterdir())


@pytest.mark.parametrize("task", ["lint:markdown", "pre-commit"])
def test_pre_commit_includes_untracked_paths_with_spaces(task_repo, task):
    calls = _calls(task_repo, task)
    command = next(call["args"] for call in calls if "--files" in call["args"])
    assert command[-2:] == ["tracked.md", "draft note.md"]


def test_python_lint_selects_shared_hooks(task_repo):
    calls = _calls(task_repo, "lint:python")
    commands = [call["args"] for call in calls if "pre-commit" in call["args"]]
    assert commands == [
        [
            "run",
            "pre-commit",
            "run",
            hook,
            "--files",
            "tracked.md",
            "draft note.md",
        ]
        for hook in ("ruff", "ruff-format", "pylint")
    ]


@pytest.mark.parametrize(
    ("task", "files"),
    [
        ("test:python", []),
        (
            "test:agent-tooling",
            [".test/test_agent_tooling.py", ".test/test_portable_hook.py"],
        ),
    ],
)
def test_pytest_tasks_forward_selection_arguments(task_repo, task, files):
    calls = _calls(task_repo, task, "--", "-k", "some or other", "--maxfail=1")
    commands = [call["args"] for call in calls if "pytest" in call["args"]]
    assert commands == [
        ["run", "pytest", *files, "-k", "some or other", "--maxfail=1"]
    ]


def test_ci_hook_skip_preserves_explicit_user_skips(task_repo, monkeypatch):
    monkeypatch.setenv("SKIP", "check-added-large-files")
    calls = _calls(task_repo, "pre-commit", "SKIP_HOOKS=stylua")
    command = next(call for call in calls if "--files" in call["args"])
    assert command["env"]["SKIP"] == "check-added-large-files,stylua"


def test_renovate_uses_a_pinned_package_even_with_a_global_validator(task_repo):
    calls = _calls(task_repo, "renovate")
    assert not any(
        call["tool"] == "renovate-config-validator" for call in calls
    )
    command = next(call["args"] for call in calls if call["tool"] == "npx")
    assert re.fullmatch(
        r"renovate@\d+\.\d+\.\d+", command[command.index("--package") + 1]
    )
    assert command[-2:] == ["renovate-config-validator", "--strict"]


def test_generator_failure_cannot_be_hidden_by_a_matching_diff(task_repo):
    script = task_repo / ".test/gen_agents_map.py"
    script.parent.mkdir()
    script.write_text('print("same")\nraise SystemExit(7)\n', encoding="utf-8")
    (task_repo / "AGENTS.md").write_text("same\n", encoding="utf-8")
    completed = _run(task_repo, "docs:agents:check")
    assert completed.returncode != 0
    assert "exit status 7" in completed.stderr


@pytest.mark.parametrize("authenticated", [True, False])
def test_dependency_upgrade_checks_access_before_ordered_updates(
    task_repo, authenticated
):
    _nvim_config(task_repo)
    script = task_repo / ".github/scripts/update_dependencies.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        RECORDER + ("\nraise SystemExit(9)\n" if not authenticated else ""),
        encoding="utf-8",
    )
    completed = _run(task_repo, "deps-upgrade")
    calls = _read_calls(task_repo)
    operations = [call["args"] for call in calls if call["tool"] != "git"]
    assert operations[:3] == [
        [
            "sync",
            "--locked",
            "--no-build",
            "--no-install-project",
            "--no-dev",
            "--managed-python",
            "--quiet",
        ],
        ["run", "pre-commit", "--version"],
        ["check"],
    ]
    if not authenticated:
        assert completed.returncode != 0
        assert len(operations) == 3
        return
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert operations[3] == ["lock", "--upgrade"]
    assert operations[4][0] == "sync"
    updates = [command for command in operations[5:] if command[0] != "sync"]
    assert updates == [
        ["run", "python", ".github/scripts/update_dependencies.py", "ansible"],
        [
            "run",
            "ansible-galaxy",
            "collection",
            "install",
            "-r",
            "requirements.yml",
            "--upgrade",
        ],
        [
            "run",
            "python",
            ".github/scripts/update_dependencies.py",
            "pre-commit",
        ],
        ["run", "python", ".github/scripts/update_dependencies.py", "npm"],
        ["--headless", '+lua dofile(".github/scripts/update_nvim.lua")'],
        [
            "run",
            next(call["args"][1] for call in calls if call["tool"] == "go"),
            "run",
            "--update",
            "--verify-comment",
            "tracked.md",
            "draft note.md",
        ],
        [
            "run",
            "python",
            ".github/scripts/update_dependencies.py",
            "repository",
        ],
    ]
    pinact = next(call["args"][1] for call in calls if call["tool"] == "go")
    assert re.fullmatch(
        r"github.com/suzuki-shunsuke/pinact/v5/cmd/pinact@v5\.\d+\.\d+", pinact
    )
    environment = next(call["env"] for call in calls if call["tool"] == "nvim")
    assert environment["NVIM_USE_MASON"] == "auto"
    assert environment["NVIM_APPNAME"] == "nvim"
    assert environment["NVIM_DOTFILES_DISABLE_PLUGINS"] == "0"
    assert Path(environment["HOME"]).parent.parent == task_repo / "scratch"
    assert not list((task_repo / "scratch").iterdir())


@pytest.mark.parametrize("gh_available", [False, True])
def test_pinact_rejects_missing_credentials_before_running(
    task_repo, monkeypatch, gh_available
):
    isolated_bin = task_repo / "isolated-bin"
    isolated_bin.mkdir()
    (isolated_bin / "sh").symlink_to(shutil.which("sh"))
    if gh_available:
        (isolated_bin / "timeout").symlink_to(shutil.which("timeout"))
        gh = isolated_bin / "gh"
        gh.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        gh.chmod(0o755)
    monkeypatch.setenv("PATH", str(isolated_bin))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("PINACT_GITHUB_TOKEN", raising=False)
    completed = _run(task_repo, "deps-upgrade:github-actions")
    assert completed.returncode != 0
    assert "GitHub authentication is required" in completed.stderr
    assert "command not found" not in completed.stderr
    assert not (task_repo / "calls.jsonl").exists()
