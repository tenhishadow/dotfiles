"""Regression tests for instruction discovery and provider references."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_instruction_refs


def _write(root: Path, relative: str, content: str = "# Instructions\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class InstructionReferencesTest(unittest.TestCase):
    """Keep hidden source paths and provider discovery in the validation scope."""

    def test_hidden_repository_paths_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for prefix in (".agents", ".claude", ".github", ".test"):
                with self.subTest(prefix=prefix):
                    ref = f"{prefix}/missing.md"
                    self.assertTrue(
                        check_instruction_refs.check_paths(root, f"`{ref}`")
                    )
                    _write(root, ref)
                    self.assertEqual(
                        [], check_instruction_refs.check_paths(root, f"[guide]({ref})")
                    )

    def test_repository_globs_and_external_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, ".agents/skills/example/SKILL.md")
            text = (
                "Read `.agents/skills/*/SKILL.md`; ignore `/etc/missing.conf`, "
                "`~/.codex/config.toml`, and "
                "[upstream](https://example.com/missing.md)."
            )
            self.assertEqual([], check_instruction_refs.check_paths(root, text))

    def test_managed_skills_are_scanned_but_generated_workspaces_are_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            managed = _write(root, "dotfiles/.agents/skills/example/SKILL.md")
            _write(root, ".test/nvim/.config/nvim/AGENTS.md")
            _write(root, ".venv/AGENTS.md")
            self.assertEqual([managed], check_instruction_refs.doc_files(root))

    def test_native_imports_resolve_relative_to_the_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, "CLAUDE.md", "@AGENTS.md\n")
            _write(root, "GEMINI.md", "@./AGENTS.md\n")
            self.assertEqual(
                2, len(check_instruction_refs.check_provider_adapters(root))
            )
            _write(root, "AGENTS.md")
            self.assertEqual([], check_instruction_refs.check_provider_adapters(root))

    def test_claude_skill_links_must_resolve_to_the_canonical_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root, ".agents/skills/example/SKILL.md")
            alias = root / ".claude/skills/example"
            alias.parent.mkdir(parents=True)
            self.assertTrue(check_instruction_refs.check_provider_adapters(root))
            for target in ("../../.agents/skills/missing", "../../.agents/skills"):
                with self.subTest(target=target):
                    alias.symlink_to(target)
                    self.assertTrue(
                        check_instruction_refs.check_provider_adapters(root)
                    )
                    alias.unlink()
            alias.symlink_to("../../.agents/skills/example")
            self.assertEqual([], check_instruction_refs.check_provider_adapters(root))


if __name__ == "__main__":
    unittest.main()
