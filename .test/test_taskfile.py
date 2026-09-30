"""Exercise Task command boundaries with local recorder executables."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
        "XDG_CACHE_HOME", "GOENV", "NVIM_USE_MASON", "NVIM_TS_INSTALL", "SKIP"
    )},
}
with open(os.environ["TASK_TEST_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(record) + "\\n")
if name == "git" and "ls-files" in sys.argv:
    sys.stdout.write("tracked.md\\0draft note.md\\0")
"""


class TaskfileBoundaryTest(unittest.TestCase):
    """Keep default apply, check, and validation commands scoped correctly."""

    def setUp(self) -> None:
        self.assertIsNotNone(TASK_BINARY, "Install Task to run task boundary tests.")
        directory = Path(tempfile.mkdtemp(prefix="dotfiles-task-"))
        self.addCleanup(shutil.rmtree, directory)
        self.root = directory / "checkout with spaces"
        self.root.mkdir()
        shutil.copyfile(ROOT / "Taskfile.yml", self.root / "Taskfile.yml")
        binary_directory = self.root / "bin"
        binary_directory.mkdir()
        for name in (
            "uv",
            "git",
            "sudo",
            "docker",
            "nvim",
            "node",
            "npx",
            "renovate-config-validator",
        ):
            executable = binary_directory / name
            executable.write_text(RECORDER, encoding="utf-8")
            executable.chmod(0o755)
        self.log = self.root / "calls.jsonl"
        self.environment = {
            **os.environ,
            "PATH": f"{binary_directory}{os.pathsep}{os.environ['PATH']}",
            "TASK_TEST_LOG": str(self.log),
            "UV_NO_SYNC": "false",
            "XDG_CONFIG_HOME": "/outside/config",
            "XDG_DATA_HOME": "/outside/data",
            "XDG_STATE_HOME": "/outside/state",
            "XDG_CACHE_HOME": "/outside/cache",
        }

    def _run(self, *arguments: str, subdirectory: bool = False) -> list[dict]:
        self.log.unlink(missing_ok=True)
        workdir = self.root
        if subdirectory:
            workdir /= "nested"
            workdir.mkdir(exist_ok=True)
        completed = subprocess.run(
            (TASK_BINARY, "--silent", *arguments),
            cwd=workdir,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_default_applies_only_user_dotfiles_from_checkout_root(self) -> None:
        calls = self._run("--", "--tags", "links", subdirectory=True)
        playbooks = [call for call in calls if "ansible-playbook" in call["args"]]
        self.assertEqual(1, len(playbooks))
        self.assertEqual(
            ["run", "ansible-playbook", "playbook_install.yml", "--tags", "links"],
            playbooks[0]["args"],
        )
        self.assertTrue(all(call["cwd"] == str(self.root) for call in calls))
        self.assertFalse(any(call["tool"] == "sudo" for call in calls))

    def test_all_preserves_order_and_sets_up_dependencies_once(self) -> None:
        calls = self._run("all")
        self.assertEqual(1, sum(call["args"][0] == "sync" for call in calls))
        self.assertEqual(1, sum("ansible-galaxy" in call["args"] for call in calls))
        self.assertEqual(
            [
                "playbook_install.yml",
                "playbook_system.yml",
                "playbook_browser_policies.yml",
            ],
            [call["args"][2] for call in calls if "ansible-playbook" in call["args"]],
        )

    def test_check_tasks_preserve_flags_and_quoted_cli_arguments(self) -> None:
        for task in ("dotfiles:check", "system:check", "browser-policies:check"):
            with self.subTest(task=task):
                calls = self._run(task, "--", "--extra-vars", '{"value":"two words"}')
                playbook = next(
                    call for call in calls if "ansible-playbook" in call["args"]
                )
                self.assertIn("--check", playbook["args"])
                self.assertIn("--diff", playbook["args"])
                self.assertIn('{"value":"two words"}', playbook["args"])

    def test_python_sync_respects_the_container_mirror_environment(self) -> None:
        self.environment["UV_NO_SYNC"] = "true"
        calls = self._run("all")
        self.assertFalse(any(call["args"][0] == "sync" for call in calls))

    def test_superlinter_quotes_mounts_and_reuses_the_latest_image_runner(self) -> None:
        envfile = self.root / ".test/system/local.env"
        envfile.parent.mkdir(parents=True)
        envfile.write_text("TEST_MIRROR=private\n", encoding="utf-8")
        calls = self._run("superlinter:latest")
        command = next(call["args"] for call in calls if call["args"][0] == "run")
        self.assertIn(f"{self.root}:/tmp/lint", command)
        self.assertIn(
            f"{self.root}/.test/system/local.env.example:"
            "/tmp/lint/.test/system/local.env:ro",
            command,
        )
        self.assertEqual("ghcr.io/super-linter/super-linter:slim-latest", command[-1])

    def test_neovim_compat_ignores_exported_user_xdg_paths(self) -> None:
        config = self.root / "dotfiles/.config/nvim"
        config.mkdir(parents=True)
        (config / "init.lua").touch()
        calls = self._run("test:nvim:compat", subdirectory=True)
        environment = next(call["env"] for call in calls if call["tool"] == "nvim")
        for variable, suffix in (
            ("HOME", ".home"),
            ("XDG_CONFIG_HOME", ".config"),
            ("XDG_DATA_HOME", ".data"),
            ("XDG_STATE_HOME", ".state"),
            ("XDG_CACHE_HOME", ".cache"),
        ):
            with self.subTest(variable=variable):
                self.assertEqual(
                    str(self.root / ".test/nvim" / suffix), environment[variable]
                )
        self.assertEqual("off", environment["NVIM_USE_MASON"])

    def test_failed_neovim_upgrade_cannot_publish_a_partial_lock(self) -> None:
        config = self.root / "dotfiles/.config/nvim"
        (config / "lua/plugins").mkdir(parents=True)
        lock = config / "lazy-lock.json"
        lock.write_text('{"original": true}\n', encoding="utf-8")
        workspace_parent = self.root / "scratch"
        workspace_parent.mkdir()
        self.environment["TMPDIR"] = str(workspace_parent)
        (self.root / "bin/nvim").write_text(
            RECORDER + '\n(Path(os.environ["XDG_CONFIG_HOME"]) / "nvim/lazy-lock.json")'
            '.write_text("partial update\\n", encoding="utf-8")\n'
            "raise SystemExit(9)\n",
            encoding="utf-8",
        )

        completed = subprocess.run(
            (TASK_BINARY, "--silent", "deps-upgrade:nvim"),
            cwd=self.root,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("exit status 9", completed.stderr)
        self.assertEqual('{"original": true}\n', lock.read_text())
        self.assertEqual([], list(workspace_parent.iterdir()))

    def test_pre_commit_includes_untracked_paths_with_spaces(self) -> None:
        for task in ("lint:markdown", "pre-commit"):
            with self.subTest(task=task):
                calls = self._run(task)
                command = next(
                    call["args"] for call in calls if "--files" in call["args"]
                )
                self.assertEqual(["tracked.md", "draft note.md"], command[-2:])

    def test_ci_hook_skip_preserves_explicit_user_skips(self) -> None:
        self.environment["SKIP"] = "check-added-large-files"
        calls = self._run("pre-commit", "SKIP_HOOKS=stylua")
        command = next(call for call in calls if "--files" in call["args"])
        self.assertEqual("check-added-large-files,stylua", command["env"]["SKIP"])

    def test_renovate_uses_a_pinned_package_even_with_a_global_validator(self) -> None:
        calls = self._run("renovate")
        self.assertFalse(
            any(call["tool"] == "renovate-config-validator" for call in calls)
        )
        command = next(call["args"] for call in calls if call["tool"] == "npx")
        self.assertRegex(command[command.index("--package") + 1], r"^renovate@\d+\.")
        self.assertEqual(["renovate-config-validator", "--strict"], command[-2:])

    def test_generator_failure_cannot_be_hidden_by_a_matching_diff(self) -> None:
        script = self.root / ".test/gen_agents_map.py"
        script.parent.mkdir()
        script.write_text('print("same")\nraise SystemExit(7)\n', encoding="utf-8")
        (self.root / "AGENTS.md").write_text("same\n", encoding="utf-8")
        completed = subprocess.run(
            (TASK_BINARY, "--silent", "docs:agents:check"),
            cwd=self.root,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("exit status 7", completed.stderr)


if __name__ == "__main__":
    unittest.main()
