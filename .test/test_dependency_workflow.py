"""Exercise the credential boundary of the weekly dependency publisher."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
import yaml

CI_FILES = {
    ".github/workflows/ansible.yml": (
        "name: Check\non: push\npermissions:\n  contents: read\n"
        "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        f"      - uses: actions/checkout@{'1' * 40} # v1.2.3\n"
    ),
    ".github/actions/setup/action.yml": (
        "name: Setup\ndescription: Setup\nruns:\n  using: composite\n  steps:\n"
        f"    - uses: astral-sh/setup-uv@{'1' * 40} # v1.2.3\n"
        "      with:\n"
        "        # renovate: datasource=github-releases depName=astral-sh/uv\n"
        '        version: "1.2.3"\n'
    ),
}
DEPENDENCY_FILES = (
    *CI_FILES,
    ".github/tools/commitlint/package.json",
    ".github/tools/commitlint/package-lock.json",
    ".pre-commit-config.yaml",
    "Taskfile.yml",
    "pyproject.toml",
    "requirements.yml",
    "uv.lock",
    "dotfiles/.config/nvim/lazy-lock.json",
    "dotfiles/.local/share/codex-cli/locked/package.json",
    "dotfiles/.local/share/codex-cli/locked/package-lock.json",
    "dotfiles/.local/share/codex-mcp/context7/package.json",
    "dotfiles/.local/share/codex-mcp/context7/package-lock.json",
)


def _git(repository, *args):
    return subprocess.check_output(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=repository,
        stderr=subprocess.PIPE,
        timeout=30,
    )


@pytest.fixture(name="publisher")
def _publisher(tmp_path, repo_root, monkeypatch):
    workflow = yaml.safe_load(
        (repo_root / ".github/workflows/dependencies.yml").read_text()
    )
    script = next(
        step["run"]
        for step in workflow["jobs"]["publish"]["steps"]
        if step.get("id") == "apply"
    )
    repository = tmp_path / "repository"
    repository.mkdir()
    runtime = tmp_path / "runtime"
    artifact = runtime / "dependency-artifact/dependencies.patch"
    artifact.parent.mkdir(parents=True)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("RUNNER_TEMP", str(runtime))
    monkeypatch.setenv("DEPENDENCY_PATHS", workflow["env"]["DEPENDENCY_PATHS"])
    _git(repository, "init", "--quiet")
    for name in (*DEPENDENCY_FILES, "README.md"):
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(CI_FILES.get(name, "original\n"), encoding="utf-8")
    _git(repository, "add", ".")
    return repository, artifact, script


def _export_patch(repository, artifact):
    artifact.write_bytes(_git(repository, "diff", "--binary", "--no-renames"))
    _git(repository, "checkout", "--", ".")


def _apply_patch(repository, script):
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_non_ci_dependency_changes_are_applied_as_data(publisher):
    repository, artifact, script = publisher
    contents = "updated $(touch unexpected-execution)\n"
    names = [name for name in DEPENDENCY_FILES if name not in CI_FILES]
    for name in names:
        (repository / name).write_text(contents, encoding="utf-8")
    _export_patch(repository, artifact)

    result = _apply_patch(repository, script)

    assert result.returncode == 0, result.stderr
    for name in names:
        assert (repository / name).read_text() == contents, name
    assert not (repository / "unexpected-execution").exists()


def test_existing_action_and_annotated_bootstrap_pins_can_update(publisher):
    repository, artifact, script = publisher
    for name, original in CI_FILES.items():
        (repository / name).write_text(
            original.replace("1" * 40, "2" * 40).replace("1.2.3", "2.3.4"),
            encoding="utf-8",
        )
    _export_patch(repository, artifact)

    result = _apply_patch(repository, script)

    assert result.returncode == 0, result.stderr
    for name in CI_FILES:
        assert "2" * 40 in (repository / name).read_text()


@pytest.mark.parametrize(
    ("name", "old", "new"),
    [
        pytest.param(
            ".github/workflows/ansible.yml",
            "on: push",
            "on: pull_request_target",
            id="privileged-trigger",
        ),
        pytest.param(
            ".github/workflows/ansible.yml",
            "contents: read",
            "contents: write",
            id="write-permission",
        ),
        pytest.param(
            ".github/workflows/ansible.yml",
            "actions/checkout@",
            "attacker/checkout@",
            id="action-repository",
        ),
        pytest.param(
            ".github/workflows/ansible.yml",
            "    steps:",
            "    env:\n      KEY: ${{ secrets.PRIVATE_KEY }}\n    steps:",
            id="credential-exposure",
        ),
        pytest.param(
            ".github/actions/setup/action.yml",
            "depName=astral-sh/uv",
            "depName=attacker/uv",
            id="bootstrap-repository",
        ),
        pytest.param(
            ".github/actions/setup/action.yml",
            'version: "1.2.3"',
            'version: "${{ secrets.PRIVATE_KEY }}"',
            id="bootstrap-expression",
        ),
    ],
)
def test_ci_behavior_changes_are_rejected(publisher, name, old, new):
    repository, artifact, script = publisher
    (repository / name).write_text(
        CI_FILES[name].replace(old, new), encoding="utf-8"
    )
    _export_patch(repository, artifact)

    result = _apply_patch(repository, script)

    assert result.returncode != 0
    assert "CI changes must only update" in result.stderr


def test_mixed_patch_is_rejected_before_any_file_is_applied(publisher):
    repository, artifact, script = publisher
    for name in ("uv.lock", "README.md"):
        (repository / name).write_text("unexpected\n", encoding="utf-8")
    _export_patch(repository, artifact)

    result = _apply_patch(repository, script)

    assert result.returncode != 0
    assert "outside tracked dependency paths" in result.stderr
    assert _git(repository, "diff") == b""
    assert (repository / "uv.lock").read_text() == "original\n"


def test_new_files_are_rejected_even_inside_dependency_directories(publisher):
    repository, artifact, script = publisher
    path = repository / ".github/workflows/injected.yml"
    path.write_text("unexpected\n", encoding="utf-8")
    _git(repository, "add", "--intent-to-add", str(path))
    artifact.write_bytes(_git(repository, "diff", "--binary", "--no-renames"))
    _git(repository, "rm", "--force", str(path))

    result = _apply_patch(repository, script)

    assert result.returncode != 0
    assert not path.exists()


@pytest.mark.parametrize("mode", ["deleted", "symlink", "executable"])
def test_dependencies_must_remain_regular_nonexecutable_files(publisher, mode):
    repository, artifact, script = publisher
    path = repository / "uv.lock"
    if mode == "executable":
        path.chmod(0o755)
    else:
        path.unlink()
        if mode == "symlink":
            path.symlink_to("README.md")
    _export_patch(repository, artifact)

    result = _apply_patch(repository, script)

    assert result.returncode != 0
    assert "must remain regular" in result.stderr
