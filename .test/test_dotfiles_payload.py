"""Black-box contracts for portable user dotfiles behavior."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASHRC = REPOSITORY_ROOT / "dotfiles" / ".bashrc"
GLOBAL_GITIGNORE = REPOSITORY_ROOT / "dotfiles" / ".gitignore"
MPLAYER_CONFIG = REPOSITORY_ROOT / "dotfiles" / ".mplayer" / "config"


class DotfilesPayloadTest(unittest.TestCase):
    """Verify security and startup contracts at their executable boundaries."""

    def test_neovim_terraform_runtime_state_is_repository_ignored(self) -> None:
        cases = {
            ".test/nvim/terraform/.terraform/terraform.tfstate": 0,
            ".test/nvim/terragrunt/.terraform/plugin-cache/example": 0,
            ".test/nvim/terraform/.terraform/.gitkeep": 1,
            ".test/nvim/terragrunt/.terraform/.gitkeep": 1,
        }
        for candidate, expected_returncode in cases.items():
            with self.subTest(candidate=candidate):
                result = subprocess.run(
                    [
                        "git",
                        "-c",
                        "core.excludesFile=/dev/null",
                        "check-ignore",
                        "--quiet",
                        "--no-index",
                        candidate,
                    ],
                    cwd=REPOSITORY_ROOT,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(expected_returncode, result.returncode)

    def test_terraform_secret_files_are_globally_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repository,
                check=True,
                timeout=10,
            )

            for candidate in (
                "terraform.tfvars",
                "production.auto.tfvars",
                "production.tfvars.json",
                "terraform.tfstate",
                "tfplan",
                "production.tfplan",
                ".terraform.d/credentials.tfrc.json",
            ):
                with self.subTest(candidate=candidate):
                    result = subprocess.run(
                        [
                            "git",
                            "-c",
                            f"core.excludesFile={GLOBAL_GITIGNORE}",
                            "check-ignore",
                            "--quiet",
                            "--no-index",
                            candidate,
                        ],
                        cwd=repository,
                        check=False,
                        timeout=10,
                    )
                    self.assertEqual(0, result.returncode)

            result = subprocess.run(
                [
                    "git",
                    "-c",
                    f"core.excludesFile={GLOBAL_GITIGNORE}",
                    "check-ignore",
                    "--quiet",
                    "--no-index",
                    "example.tfvars.example",
                ],
                cwd=repository,
                check=False,
                timeout=10,
            )
            self.assertEqual(1, result.returncode)

    def test_interactive_startup_does_not_run_completion_generators(self) -> None:
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
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
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
                    str(BASHRC),
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

            self.assertFalse(
                trace_path.exists(),
                "interactive startup eagerly invoked a completion generator",
            )

    def test_mplayer_baseline_uses_auto_selection(self) -> None:
        config_text = MPLAYER_CONFIG.read_text(encoding="utf-8")
        self.assertNotRegex(config_text, r"(?im)^\s*vo\s*=")
        self.assertNotRegex(config_text, r"(?im)^\s*vc\s*=")

    @unittest.skipUnless(shutil.which("mplayer"), "MPlayer is not installed")
    def test_mplayer_baseline_parses_when_mplayer_is_available(self) -> None:
        config_text = MPLAYER_CONFIG.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary_directory:
            mplayer_directory = Path(temporary_directory) / ".mplayer"
            mplayer_directory.mkdir()
            (mplayer_directory / "config").write_text(config_text, encoding="utf-8")
            environment = os.environ.copy()
            environment["HOME"] = temporary_directory

            result = subprocess.run(
                ["mplayer", "-vo", "help"],
                check=False,
                capture_output=True,
                env=environment,
                text=True,
                timeout=10,
            )
            output = result.stdout + result.stderr
            self.assertNotIn("Failed to read", output)
            self.assertNotIn("unknown option", output.lower())
            self.assertNotRegex(output, r"(?i)at line \d+")


if __name__ == "__main__":
    unittest.main()
