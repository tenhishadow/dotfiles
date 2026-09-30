"""Exercise the credential boundary of the weekly dependency publisher."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/dependencies.yml").read_text())
APPLY_SCRIPT = next(
    step["run"]
    for step in WORKFLOW["jobs"]["publish"]["steps"]
    if step.get("id") == "apply"
)
DEPENDENCY_FILES = (
    ".github/actions/setup/action.yml",
    ".github/workflows/ansible.yml",
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


class DependencyPatchTest(unittest.TestCase):
    """Run the actual publisher script with patches from disposable Git indexes."""

    def setUp(self) -> None:
        workspace = Path(tempfile.mkdtemp(prefix="dependency-patch-test-"))
        self.addCleanup(shutil.rmtree, workspace)
        self.repository = workspace / "repository"
        self.repository.mkdir()
        self.runtime = workspace / "runtime"
        self.artifact = self.runtime / "dependency-artifact/dependencies.patch"
        self.artifact.parent.mkdir(parents=True)
        self.git("init", "--quiet")
        for name in (*DEPENDENCY_FILES, "README.md"):
            path = self.repository / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(CI_FILES.get(name, "original\n"), encoding="utf-8")
        self.git("add", ".")

    def git(self, *args: str) -> bytes:
        """Run Git without relying on a real commit or the user's Git configuration."""

        return subprocess.check_output(
            ["git", "-c", "core.autocrlf=false", *args],
            cwd=self.repository,
            env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull},
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def export_patch(self) -> None:
        """Restore the checkout after capturing a potentially hostile patch."""

        self.artifact.write_bytes(self.git("diff", "--binary", "--no-renames"))
        self.git("checkout", "--", ".")

    def apply_patch(self) -> subprocess.CompletedProcess[str]:
        """Execute the publisher's real inline Python, without credentials."""

        return subprocess.run(
            [sys.executable, "-c", APPLY_SCRIPT],
            cwd=self.repository,
            env={
                **os.environ,
                "GIT_CONFIG_GLOBAL": os.devnull,
                "RUNNER_TEMP": str(self.runtime),
                "DEPENDENCY_PATHS": WORKFLOW["env"]["DEPENDENCY_PATHS"],
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_applies_non_ci_dependency_surfaces_as_data(self) -> None:
        contents = "updated $(touch unexpected-execution)\n"
        names = [name for name in DEPENDENCY_FILES if name not in CI_FILES]
        for name in names:
            (self.repository / name).write_text(contents, encoding="utf-8")
        self.export_patch()

        result = self.apply_patch()

        self.assertEqual(0, result.returncode, result.stderr)
        for name in names:
            with self.subTest(path=name):
                self.assertEqual(contents, (self.repository / name).read_text())
        self.assertFalse((self.repository / "unexpected-execution").exists())

    def test_allows_existing_action_and_annotated_bootstrap_pin_updates(self) -> None:
        for name, original in CI_FILES.items():
            updated = original.replace("1" * 40, "2" * 40).replace("1.2.3", "2.3.4")
            (self.repository / name).write_text(updated, encoding="utf-8")
        self.export_patch()

        result = self.apply_patch()

        self.assertEqual(0, result.returncode, result.stderr)
        for name in CI_FILES:
            self.assertIn("2" * 40, (self.repository / name).read_text())

    def test_rejects_ci_behavior_and_action_repository_changes(self) -> None:
        cases = {
            ".github/workflows/ansible.yml": (
                ("on: push", "on: pull_request_target"),
                ("contents: read", "contents: write"),
                ("actions/checkout@", "attacker/checkout@"),
                (
                    "    steps:",
                    "    env:\n      KEY: ${{ secrets.PRIVATE_KEY }}\n    steps:",
                ),
            ),
            ".github/actions/setup/action.yml": (
                ("depName=astral-sh/uv", "depName=attacker/uv"),
                ('version: "1.2.3"', 'version: "${{ secrets.PRIVATE_KEY }}"'),
            ),
        }
        for name, replacements in cases.items():
            for old, new in replacements:
                with self.subTest(path=name, replacement=new):
                    path = self.repository / name
                    path.write_text(CI_FILES[name].replace(old, new), encoding="utf-8")
                    self.export_patch()

                    result = self.apply_patch()

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("CI changes must only update", result.stderr)
                    path.write_text(CI_FILES[name], encoding="utf-8")
                    self.git("add", name)

    def test_rejects_mixed_patch_before_any_file_is_applied(self) -> None:
        for name in ("uv.lock", "README.md"):
            (self.repository / name).write_text("unexpected\n", encoding="utf-8")
        self.export_patch()

        result = self.apply_patch()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("outside tracked dependency paths", result.stderr)
        self.assertEqual(b"", self.git("diff"))
        self.assertEqual("original\n", (self.repository / "uv.lock").read_text())

    def test_rejects_new_files_even_inside_dependency_directories(self) -> None:
        path = self.repository / ".github/workflows/injected.yml"
        path.write_text("unexpected\n", encoding="utf-8")
        self.git("add", "--intent-to-add", str(path))
        self.artifact.write_bytes(self.git("diff", "--binary", "--no-renames"))
        self.git("rm", "--force", str(path))

        result = self.apply_patch()

        self.assertNotEqual(0, result.returncode)
        self.assertFalse(path.exists())

    def test_rejects_dependency_deletion(self) -> None:
        (self.repository / "uv.lock").unlink()
        self.export_patch()

        result = self.apply_patch()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("must remain regular", result.stderr)

    def test_rejects_symlink_and_executable_modes(self) -> None:
        path = self.repository / "uv.lock"
        for mode in ("symlink", "executable"):
            with self.subTest(mode=mode):
                if mode == "symlink":
                    path.unlink()
                    path.symlink_to("README.md")
                else:
                    path.chmod(0o755)
                self.export_patch()

                result = self.apply_patch()

                self.assertNotEqual(0, result.returncode)
                self.assertIn("must remain regular", result.stderr)
                # Reinitialize only this fixture's index before the next case.
                path.unlink()
                path.write_text("original\n", encoding="utf-8")
                self.git("add", "uv.lock")


if __name__ == "__main__":
    unittest.main()
