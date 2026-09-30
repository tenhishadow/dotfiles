"""Regression tests for instruction discovery and provider references."""

import shutil
import sys
from pathlib import Path

import pytest

import check_instruction_refs


def _write(
    root: Path, relative: str, content: str = "# Instructions\n"
) -> Path:
    """Create a source file and any required fixture directories."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize("prefix", [".agents", ".claude", ".github", ".test"])
def test_hidden_repository_paths_are_checked(tmp_path: Path, prefix):
    ref = f"{prefix}/missing.md"
    assert check_instruction_refs.check_paths(tmp_path, f"`{ref}`")
    _write(tmp_path, ref)
    assert not check_instruction_refs.check_paths(tmp_path, f"[guide]({ref})")


def test_repository_globs_and_external_paths(tmp_path: Path):
    _write(tmp_path, ".agents/skills/example/SKILL.md")
    text = (
        "Read `.agents/skills/*/SKILL.md`; ignore `/etc/missing.conf`, "
        "`~/.codex/config.toml`, and "
        "[upstream](https://example.com/missing.md)."
    )
    assert not check_instruction_refs.check_paths(tmp_path, text)


@pytest.mark.parametrize(
    ("reference", "optional"),
    [
        (".test/nvim/.cache", True),
        (".test/system/local.env", True),
        (".test/nvim/.cache-missing", False),
        (".test/nvim/smoke.lua", False),
        (".test/system/local.env.example", False),
        (".test/generated/missing.py", False),
        (".test/nvim/.cache/missing.md", False),
    ],
)
def test_optional_runtime_paths_do_not_hide_missing_sources(
    tmp_path: Path, reference, optional
):
    _write(
        tmp_path,
        ".gitignore",
        ".test/nvim/.cache/\n.test/system/local.env\n.test/generated/*\n",
    )
    errors = check_instruction_refs.check_paths(tmp_path, f"`{reference}`")
    assert bool(errors) is not optional


def test_current_instructions_resolve_in_a_clean_source_export(
    run_command, tmp_path: Path, repo_root: Path
):
    files = run_command(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo_root,
        check=True,
    ).stdout
    for name in sorted(set(files.split("\0")) - {""}):
        source = repo_root / name
        # Deleted tracked files are absent from the current publication set.
        if not source.exists() and not source.is_symlink():
            continue
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)
    assert not (tmp_path / ".test/nvim/.cache").exists()
    assert not (tmp_path / ".test/system/local.env").exists()
    result = run_command(
        [sys.executable, str(tmp_path / ".test/check_instruction_refs.py")],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_managed_skills_are_scanned_but_generated_workspaces_are_not(
    tmp_path: Path,
):
    managed = _write(tmp_path, "dotfiles/.agents/skills/example/SKILL.md")
    _write(tmp_path, ".test/nvim/.config/nvim/AGENTS.md")
    _write(tmp_path, ".venv/AGENTS.md")
    assert check_instruction_refs.doc_files(tmp_path) == [managed]


def test_native_imports_resolve_relative_to_the_adapter(tmp_path: Path):
    _write(tmp_path, "CLAUDE.md", "@AGENTS.md\n")
    _write(tmp_path, "GEMINI.md", "@./AGENTS.md\n")
    assert len(check_instruction_refs.check_provider_adapters(tmp_path)) == 2
    _write(tmp_path, "AGENTS.md")
    assert not check_instruction_refs.check_provider_adapters(tmp_path)


@pytest.mark.parametrize(
    "target",
    [
        None,
        "../../.agents/skills/missing",
        "../../.agents/skills",
        "../../.agents/skills/example",
    ],
    ids=["missing-alias", "missing-target", "wrong-directory", "canonical"],
)
def test_claude_skill_links_must_resolve_to_the_canonical_skill(
    tmp_path: Path, target
):
    _write(tmp_path, ".agents/skills/example/SKILL.md")
    alias = tmp_path / ".claude/skills/example"
    alias.parent.mkdir(parents=True)
    if target is not None:
        alias.symlink_to(target)
    errors = check_instruction_refs.check_provider_adapters(tmp_path)
    assert bool(errors) == (target != "../../.agents/skills/example")
