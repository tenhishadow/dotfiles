"""Keep the English guard aligned with Git's local publication candidate."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from check_repo_english import first_foreign_letter


@pytest.fixture(name="repository")
def fixture_repository(run_command, tmp_path: Path, monkeypatch) -> Path:
    """Create a disposable Git publication set."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "repository"
    root.mkdir()
    run_command(["git", "init", "--quiet", str(root)], check=True)
    return root


def _check(
    run_command, repository: Path, repo_root: Path
) -> subprocess.CompletedProcess[str]:
    """Run the real scanner against only the disposable Git publication set."""
    return run_command(
        [sys.executable, str(repo_root / ".test/check_repo_english.py")],
        cwd=repository,
    )


def test_untracked_hidden_extensionless_source_is_checked(
    run_command, repository, repo_root
):
    path = repository / ".agents/instructions"
    path.parent.mkdir()
    path.write_text(
        "English first line\n\u041f\u0440\u0438\u0432\u0435\u0442\n",
        encoding="utf-8",
    )
    result = _check(run_command, repository, repo_root)
    assert result.returncode == 1
    assert ".agents/instructions:2:" in result.stdout
    assert "U+041F" in result.stdout


def test_non_ascii_filename_is_checked_with_english_content(
    run_command, repository, repo_root
):
    (repository / "\u0422\u0435\u0441\u0442.md").write_text(
        "English\n", encoding="utf-8"
    )
    result = _check(run_command, repository, repo_root)
    assert result.returncode == 1
    assert "in file path" in result.stdout


def test_ignored_runtime_files_are_not_publication_candidates(
    run_command, repository, repo_root
):
    (repository / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    ignored = repository / "ignored"
    ignored.mkdir()
    (ignored / "runtime").write_text(
        "\u0422\u0435\u043a\u0441\u0442\n", encoding="utf-8"
    )
    assert _check(run_command, repository, repo_root).returncode == 0


def test_symlinks_check_stored_targets_without_reading_destinations(
    run_command, repository, repo_root
):
    outside = repository.parent / "private-runtime"
    outside.write_text("\u0422\u0435\u043a\u0441\u0442\n", encoding="utf-8")
    link = repository / "link"
    link.symlink_to("../private-runtime")
    assert _check(run_command, repository, repo_root).returncode == 0
    link.unlink()
    link.symlink_to("\u0422\u0435\u043a\u0441\u0442")
    result = _check(run_command, repository, repo_root)
    assert result.returncode == 1
    assert "link:1:" in result.stdout


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("English \ue0b0 \u2191 \u2500 \u200b\n".encode(), None),
        (b"binary\x00" + "\u0422".encode(), None),
        ("English\n\u0422".encode(), (2, "\u0422")),
    ],
    ids=["symbols", "binary", "foreign-prose"],
)
def test_foreign_letters_are_distinguished_from_symbols_and_binary(
    data, expected
):
    assert first_foreign_letter(data) == expected
