"""Keep the English guard aligned with Git's local publication candidate."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_repo_english import first_foreign_letter

CHECKER = Path(__file__).with_name("check_repo_english.py")


class EnglishGuardTest(unittest.TestCase):
    """Scan new source and stored links while ignoring generated state."""

    def setUp(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="dotfiles-english-"))
        self.addCleanup(shutil.rmtree, directory)
        self.root = directory / "repository"
        self.root.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", str(self.root)],
            check=True,
            capture_output=True,
            timeout=10,
        )

    def _check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER)],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_untracked_hidden_extensionless_source_is_checked(self) -> None:
        path = self.root / ".agents/instructions"
        path.parent.mkdir()
        path.write_text(
            "English first line\n\u041f\u0440\u0438\u0432\u0435\u0442\n",
            encoding="utf-8",
        )

        result = self._check()

        self.assertEqual(1, result.returncode)
        self.assertIn(".agents/instructions:2:", result.stdout)
        self.assertIn("U+041F", result.stdout)

    def test_non_ascii_filename_is_checked_even_when_content_is_english(self) -> None:
        (self.root / "\u0422\u0435\u0441\u0442.md").write_text(
            "English\n", encoding="utf-8"
        )

        result = self._check()

        self.assertEqual(1, result.returncode)
        self.assertIn("in file path", result.stdout)

    def test_ignored_runtime_files_are_not_publication_candidates(self) -> None:
        (self.root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        ignored = self.root / "ignored"
        ignored.mkdir()
        (ignored / "runtime").write_text(
            "\u0422\u0435\u043a\u0441\u0442\n", encoding="utf-8"
        )

        self.assertEqual(0, self._check().returncode)

    def test_symlinks_check_stored_targets_without_reading_destinations(self) -> None:
        outside = self.root.parent / "private-runtime"
        outside.write_text("\u0422\u0435\u043a\u0441\u0442\n", encoding="utf-8")
        link = self.root / "link"
        link.symlink_to("../private-runtime")
        self.assertEqual(0, self._check().returncode)

        link.unlink()
        link.symlink_to("\u0422\u0435\u043a\u0441\u0442")
        result = self._check()
        self.assertEqual(1, result.returncode)
        self.assertIn("link:1:", result.stdout)

    def test_symbols_and_binary_data_do_not_become_foreign_prose(self) -> None:
        for data in (
            "English \ue0b0 \u2191 \u2500 \u200b\n".encode(),
            b"binary\x00" + "\u0422".encode(),
        ):
            with self.subTest(data=data):
                self.assertIsNone(first_foreign_letter(data))
        self.assertEqual(
            (2, "\u0422"), first_foreign_letter("English\n\u0422".encode())
        )


if __name__ == "__main__":
    unittest.main()
