"""Network-free contract tests for repository dependency upgrades."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
UPDATER_PATH = ROOT / ".github/scripts/update_dependencies.py"


def _load_updater() -> object:
    spec = importlib.util.spec_from_file_location("update_dependencies", UPDATER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load dependency updater from {UPDATER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


update_dependencies = _load_updater()


def _task_block(taskfile: str, name: str) -> str:
    """Return one top-level Taskfile task without parsing command YAML."""

    lines = taskfile.splitlines()
    marker = f"  {name}:"
    try:
        start = lines.index(marker)
    except ValueError as error:
        raise AssertionError(f"Taskfile task is missing: {name}") from error

    end = len(lines)
    task_heading = re.compile(r"^  [a-z0-9][a-z0-9:_-]*:$")
    for index in range(start + 1, len(lines)):
        if task_heading.fullmatch(lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


class TaskfileScalarReplacementTest(unittest.TestCase):
    """Keep Taskfile pin replacement exact and fail closed on ambiguity."""

    def test_replaces_one_named_scalar_without_reformatting(self) -> None:
        content = (
            "vars:\n"
            '  RENOVATE_VERSION: "44.48.3"\n'
            '  RENOVATE_NODE_MIN_VERSION: "24.11.0"\n'
        )

        self.assertEqual(
            (
                "vars:\n"
                '  RENOVATE_VERSION: "44.50.1"\n'
                '  RENOVATE_NODE_MIN_VERSION: "24.11.0"\n'
            ),
            update_dependencies.replace_taskfile_scalar(
                content, "RENOVATE_VERSION", "44.50.1"
            ),
        )

    def test_rejects_missing_or_duplicate_named_scalar(self) -> None:
        cases = {
            "missing": 'vars:\n  OTHER_VERSION: "1.0.0"\n',
            "duplicate": (
                'vars:\n  RENOVATE_VERSION: "44.48.3"\n  RENOVATE_VERSION: "44.49.1"\n'
            ),
        }

        for name, content in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                update_dependencies.replace_taskfile_scalar(
                    content, "RENOVATE_VERSION", "44.50.1"
                )


class RepositoryPinReplacementTest(unittest.TestCase):
    """Keep coupled tool pins updated from one resolved version set."""

    def test_replaces_renovate_version_and_node_engine_together(self) -> None:
        content = (
            "vars:\n"
            '  RENOVATE_VERSION: "44.48.3"\n'
            '  RENOVATE_NODE_MIN_VERSION: "22.13.0"\n'
            '  PINACT_VERSION: "v4.1.0"\n'
            '  SUPERLINTER_IMAGE_TAG: "slim-v8.6.0"\n'
        )
        replace_pins = vars(update_dependencies)["_replace_repository_pins"]

        self.assertEqual(
            (
                "vars:\n"
                '  RENOVATE_VERSION: "44.50.1"\n'
                '  RENOVATE_NODE_MIN_VERSION: "24.11.0"\n'
                '  PINACT_VERSION: "v4.1.1"\n'
                '  SUPERLINTER_IMAGE_TAG: "slim-v8.7.0"\n'
            ),
            replace_pins(
                content,
                update_dependencies.RepositoryPins(
                    renovate="44.50.1",
                    renovate_node_minimum="24.11.0",
                    pinact="v4.1.1",
                    super_linter="slim-v8.7.0",
                ),
            ),
        )


class NodeEngineParsingTest(unittest.TestCase):
    """Derive the checked Node minimum only from a precise engine range."""

    def test_extracts_minimum_from_caret_range(self) -> None:
        self.assertEqual(
            "24.11.0",
            update_dependencies.parse_node_engine_minimum("^24.11.0"),
        )

    def test_rejects_ambiguous_or_incomplete_ranges(self) -> None:
        for engine in (">=24", "24.x", "^24.11.0 || ^26.0.0", "*"):
            with self.subTest(engine=engine), self.assertRaises(ValueError):
                update_dependencies.parse_node_engine_minimum(engine)


class GitHubAuthenticationTest(unittest.TestCase):
    """Resolve API authentication deterministically without exposing tokens."""

    def test_gh_token_is_bounded_and_scoped_to_github_com(self) -> None:
        completed = mock.Mock(stdout="token\n")

        with mock.patch.object(
            update_dependencies.subprocess,
            "run",
            return_value=completed,
        ) as run:
            token = vars(update_dependencies)["_gh_auth_token"]()

        self.assertEqual("token\n", token)
        run.assert_called_once_with(
            ("gh", "auth", "token", "--hostname", "github.com"),
            check=True,
            capture_output=True,
            text=True,
            timeout=update_dependencies.SHORT_COMMAND_TIMEOUT_SECONDS,
        )

    def test_environment_token_precedence_avoids_gh(self) -> None:
        loader_calls = 0

        def load_token() -> str:
            nonlocal loader_calls
            loader_calls += 1
            return "unexpected"

        self.assertEqual(
            "pinact-token",
            update_dependencies.resolve_github_token(
                {
                    "PINACT_GITHUB_TOKEN": "pinact-token",
                    "GITHUB_TOKEN": "github-token",
                },
                load_token,
            ),
        )
        self.assertEqual(0, loader_calls)

    def test_falls_back_to_authenticated_gh(self) -> None:
        self.assertEqual(
            "gh-token",
            update_dependencies.resolve_github_token({}, lambda: " gh-token\n"),
        )

    def test_fails_closed_without_authentication(self) -> None:
        def missing_gh() -> str:
            raise FileNotFoundError("gh")

        with self.assertRaisesRegex(ValueError, "GitHub authentication is required"):
            update_dependencies.resolve_github_token({}, missing_gh)

    def test_validates_token_and_nonempty_core_quota(self) -> None:
        payload = {"resources": {"core": {"remaining": 42}}}

        with mock.patch.object(
            update_dependencies, "_fetch_json", return_value=payload
        ) as fetch_json:
            token = update_dependencies.validate_github_authentication(
                {"GITHUB_TOKEN": "secret"},
                lambda: "unexpected",
            )

        self.assertEqual("secret", token)
        fetch_json.assert_called_once_with(
            "https://api.github.com/rate_limit",
            github_token="secret",
        )

    def test_rejects_exhausted_or_malformed_core_quota(self) -> None:
        cases = {
            "exhausted": {"resources": {"core": {"remaining": 0}}},
            "missing": {"resources": {}},
            "boolean": {"resources": {"core": {"remaining": True}}},
        }

        for name, payload in cases.items():
            with (
                self.subTest(name=name),
                mock.patch.object(
                    update_dependencies, "_fetch_json", return_value=payload
                ),
                self.assertRaises(ValueError),
            ):
                update_dependencies.validate_github_authentication(
                    {"GITHUB_TOKEN": "secret"},
                    lambda: "unexpected",
                )


class GitHubReleaseTest(unittest.TestCase):
    """Read the latest release and surface unsupported pinact majors."""

    def test_repository_pin_resolution_enforces_supported_pinact_major(self) -> None:
        renovate = {"version": "44.50.1", "engines": {"node": "^24.11.0"}}

        def fetch_json(url: str, **_kwargs: str) -> object:
            if url.endswith("/renovate/latest"):
                return renovate
            tag = pinact_tag if "/pinact/" in url else "v8.7.0"
            return {"tag_name": tag}

        for pinact_tag in ("v5.0.0", "v6.0.0"):
            with (
                self.subTest(pinact_tag=pinact_tag),
                mock.patch.object(
                    update_dependencies, "_fetch_json", side_effect=fetch_json
                ),
            ):
                resolve = vars(update_dependencies)["_resolve_repository_pins"]
                if pinact_tag == "v5.0.0":
                    self.assertEqual(pinact_tag, resolve("secret").pinact)
                else:
                    with self.assertRaisesRegex(ValueError, "pinact major changed"):
                        resolve("secret")


class AnsibleRequirementsUpdateTest(unittest.TestCase):
    """Update exact collection versions without serializing the YAML anew."""

    def test_updates_versions_and_preserves_surrounding_formatting(self) -> None:
        content = """collections:
  # Keep this comment and field order.
  - name: ansible.posix
    version: "2.1.0"  # exact pin
    source: https://galaxy.ansible.com
  - name: community.general
    version: '13.2.0'
    source: https://galaxy.ansible.com
"""

        self.assertEqual(
            """collections:
  # Keep this comment and field order.
  - name: ansible.posix
    version: "2.2.2"  # exact pin
    source: https://galaxy.ansible.com
  - name: community.general
    version: '13.3.0'
    source: https://galaxy.ansible.com
""",
            update_dependencies.update_ansible_requirements(
                content,
                {
                    "ansible.posix": "2.2.2",
                    "community.general": "13.3.0",
                },
            ),
        )

    def test_rejects_a_requested_collection_that_is_not_unique(self) -> None:
        cases = {
            "missing": """collections:
  - name: unrelated.collection
    version: "1.0.0"
""",
            "duplicate": (
                "collections:\n"
                "  - name: ansible.posix\n"
                '    version: "2.1.0"\n'
                "  - name: ansible.posix\n"
                '    version: "2.2.0"\n'
            ),
        }

        for name, content in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                update_dependencies.update_ansible_requirements(
                    content, {"ansible.posix": "2.2.2"}
                )


class GalaxyVersionResolutionTest(unittest.TestCase):
    """Resolve stable collection versions across bounded Galaxy pages."""

    def test_follows_relative_next_link(self) -> None:
        next_link = "/api/v3/next"
        pages = (
            {"data": [{"version": "9.9.0"}], "links": {"next": next_link}},
            {"data": [{"version": "10.0.0"}], "links": {"next": None}},
        )

        with mock.patch.object(
            update_dependencies, "_fetch_json", side_effect=pages
        ) as fetch_json:
            self.assertEqual(
                "10.0.0",
                vars(update_dependencies)["_latest_collection_version"](
                    "community.general"
                ),
            )

        self.assertEqual(2, fetch_json.call_count)
        self.assertEqual(
            f"https://galaxy.ansible.com{next_link}",
            fetch_json.call_args_list[1].args[0],
        )

    def test_rejects_version_history_beyond_page_limit(self) -> None:
        page = {
            "data": [{"version": "1.0.0"}],
            "links": {"next": "/api/v3/next"},
        }

        with (
            mock.patch.object(
                update_dependencies, "_fetch_json", return_value=page
            ) as fetch_json,
            self.assertRaisesRegex(ValueError, "exceeds .* pages"),
        ):
            vars(update_dependencies)["_latest_collection_version"](
                "example.collection"
            )

        self.assertEqual(
            update_dependencies.GALAXY_VERSION_MAX_PAGES,
            fetch_json.call_count,
        )


class NpmDependencyCommandTest(unittest.TestCase):
    """Build one deterministic lock-only npm update command per manifest."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def _write_package(self, relative: Path, manifest: str = "{}\n") -> Path:
        package = self.root / relative
        package.mkdir(parents=True)
        (package / "package.json").write_text(manifest, encoding="utf-8")
        (package / "package-lock.json").write_text("{}\n", encoding="utf-8")
        return package

    def test_discovers_sorted_direct_dependencies(self) -> None:
        manifest = {
            "name": "managed-tools",
            "dependencies": {
                "zeta": "1.0.0",
                "@scope/tool": "2.0.0",
                "alpha": "3.0.0",
            },
        }

        self.assertEqual(
            ("@scope/tool", "alpha", "zeta"),
            update_dependencies.direct_npm_dependencies(manifest),
        )

    def test_builds_lock_only_exact_update_command(self) -> None:
        package_directory = Path("dotfiles/.local/share/example")
        expected = tuple(
            shlex.split(
                "npm install --package-lock-only --ignore-scripts --no-audit "
                "--no-fund --save-exact --registry=https://registry.npmjs.org/ "
                "--prefix "
                "dotfiles/.local/share/example @scope/tool@latest alpha@latest"
            )
        )

        self.assertEqual(
            expected,
            update_dependencies.build_npm_update_command(
                package_directory, ("@scope/tool", "alpha")
            ),
        )

    def test_rejects_manifest_without_a_dependency_mapping(self) -> None:
        for manifest in ({}, {"dependencies": []}, {"dependencies": {}}):
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                update_dependencies.direct_npm_dependencies(manifest)

    def test_managed_discovery_excludes_test_fixtures(self) -> None:
        discover_manifests = vars(update_dependencies)["_managed_npm_manifests"]
        managed = self._write_package(
            update_dependencies.NPM_MANIFEST_ROOTS[0] / "locked-package"
        )
        self._write_package(Path(".test/nvim/typescript"))

        self.assertEqual((managed / "package.json",), discover_manifests(self.root))

    def test_cli_reports_malformed_manifest_without_a_traceback(self) -> None:
        self._write_package(
            update_dependencies.NPM_MANIFEST_ROOTS[0], "{invalid json}\n"
        )
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            status = update_dependencies.main(("--root", str(self.root), "npm"))

        self.assertEqual(1, status)
        self.assertIn("dependency update failed:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_npm_update_refreshes_transitive_locks_after_direct_packages(self) -> None:
        self._write_package(
            update_dependencies.NPM_MANIFEST_ROOTS[0],
            '{"dependencies":{"example":"1.0.0"}}\n',
        )
        with mock.patch.object(update_dependencies.subprocess, "run") as run:
            update_dependencies.update_npm(self.root)

        self.assertEqual(("npm", "install"), run.call_args_list[0].args[0][:2])
        self.assertIn("example@latest", run.call_args_list[0].args[0])
        self.assertEqual(("npm", "update"), run.call_args_list[1].args[0][:2])
        for call in run.call_args_list:
            self.assertIn("--package-lock-only", call.args[0])
            self.assertIn("--ignore-scripts", call.args[0])
            self.assertEqual(
                update_dependencies.PACKAGE_COMMAND_TIMEOUT_SECONDS,
                call.kwargs["timeout"],
            )


class RepositoryUpdateIntegrationTest(unittest.TestCase):
    """Exercise coupled pins and annotated CI versions without network access."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.taskfile = self.root / "Taskfile.yml"
        self.taskfile.write_text(
            'vars:\n  RENOVATE_VERSION: "44.48.3"\n'
            '  RENOVATE_NODE_MIN_VERSION: "22.13.0"\n'
            '  PINACT_VERSION: "v5.0.0"\n'
            '  SUPERLINTER_IMAGE_TAG: "slim-v8.6.0"\n',
            encoding="utf-8",
        )
        self.action = self.root / ".github/actions/setup/action.yml"
        self.action.parent.mkdir(parents=True)
        self.action.write_text(
            "steps:\n  - with:\n"
            "      # renovate: datasource=github-releases depName=astral-sh/uv\n"
            '      version: "0.12.0"\n'
            '  - with:\n      version: "3.14"\n',
            encoding="utf-8",
        )
        for name, value in (
            ("validate_github_authentication", "secret"),
            (
                "_resolve_repository_pins",
                update_dependencies.RepositoryPins(
                    renovate="44.50.1",
                    renovate_node_minimum="24.11.0",
                    pinact="v5.0.0",
                    super_linter="slim-v8.7.0",
                ),
            ),
        ):
            patcher = mock.patch.object(update_dependencies, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_second_run_is_byte_identical_and_unannotated_versions_stay(self) -> None:
        with mock.patch.object(
            update_dependencies, "_latest_github_release", return_value="0.12.21"
        ) as release:
            update_dependencies.update_repository_pins(self.root)
            first = (self.taskfile.read_bytes(), self.action.read_bytes())
            update_dependencies.update_repository_pins(self.root)
            second = (self.taskfile.read_bytes(), self.action.read_bytes())
        self.assertEqual(first, second)
        self.assertIn(b'RENOVATE_VERSION: "44.50.1"', first[0])
        self.assertIn(b'version: "0.12.21"', first[1])
        self.assertIn(b'version: "3.14"', first[1])
        self.assertEqual(
            [mock.call("astral-sh/uv", "secret")] * 2, release.call_args_list
        )

    def test_resolution_failure_does_not_write(self) -> None:
        original = (self.taskfile.read_bytes(), self.action.read_bytes())
        with (
            mock.patch.object(
                update_dependencies,
                "_latest_github_release",
                side_effect=ValueError("resolution failed"),
            ),
            self.assertRaisesRegex(ValueError, "resolution failed"),
        ):
            update_dependencies.update_repository_pins(self.root)
        self.assertEqual(
            original, (self.taskfile.read_bytes(), self.action.read_bytes())
        )


class AtomicDependencyWriteTest(unittest.TestCase):
    """Keep each dependency file replacement complete and mode-preserving."""

    def test_changed_file_is_replaced_from_its_own_directory(self) -> None:
        write_if_changed = vars(update_dependencies)["_write_if_changed"]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Taskfile.yml"
            path.write_text("old\n", encoding="utf-8")
            path.chmod(0o640)
            real_replace = os.replace
            replacements: list[tuple[Path, Path]] = []

            def record_replace(
                source: str | os.PathLike[str],
                destination: str | os.PathLike[str],
            ) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                replacements.append((source_path, destination_path))
                real_replace(source_path, destination_path)

            with mock.patch.object(
                update_dependencies.os,
                "replace",
                side_effect=record_replace,
            ):
                write_if_changed(path, "old\n", "new\n")

            updated = path.read_text(encoding="utf-8")
            updated_mode = path.stat().st_mode & 0o777
            remaining_paths = tuple(Path(directory).iterdir())

        self.assertEqual("new\n", updated)
        self.assertEqual(0o640, updated_mode)
        self.assertEqual(1, len(replacements))
        self.assertEqual(path.parent, replacements[0][0].parent)
        self.assertEqual(path, replacements[0][1])
        self.assertEqual((path,), remaining_paths)

    def test_failed_replace_leaves_original_and_removes_temporary_file(self) -> None:
        write_if_changed = vars(update_dependencies)["_write_if_changed"]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Taskfile.yml"
            path.write_text("old\n", encoding="utf-8")

            with (
                mock.patch.object(
                    update_dependencies.os,
                    "replace",
                    side_effect=OSError("replace failed"),
                ),
                self.assertRaisesRegex(OSError, "replace failed"),
            ):
                write_if_changed(path, "old\n", "new\n")

            self.assertEqual("old\n", path.read_text(encoding="utf-8"))
            self.assertEqual((path,), tuple(Path(directory).iterdir()))


class DependencyUpgradeOrchestrationTest(unittest.TestCase):
    """Keep the public upgrade task complete, isolated, and mutation-only."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        cls.renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))

    def test_aggregate_runs_every_managed_dependency_surface_in_order(self) -> None:
        aggregate = _task_block(self.taskfile, "deps-upgrade")

        self.assertIn("deps: [deps-upgrade:check]", aggregate)
        self.assertEqual(
            [
                "deps-upgrade:python",
                "deps-upgrade:ansible",
                "deps-upgrade:pre-commit",
                "deps-upgrade:npm",
                "deps-upgrade:nvim",
                "deps-upgrade:github-actions",
                "deps-upgrade:repository",
            ],
            re.findall(r"^\s+- task: ([a-z0-9:_-]+)$", aggregate, re.MULTILINE),
        )
        self.assertNotIn("TASK_EXE", aggregate)
        self.assertNotIn("task: renovate", aggregate)

    def test_preflight_provisions_tools_and_validates_auth_before_updates(self) -> None:
        task = _task_block(self.taskfile, "deps-upgrade:check")

        self.assertIn("deps: [deps-os]", task)
        self.assertIn("for tool in git go npm nvim python3 timeout uv", task)
        self.assertIn(
            "timeout {{.DEPENDENCY_COMMAND_TIMEOUT}}\n"
            "        uv sync --locked --no-build --no-install-project --no-dev "
            "--managed-python --quiet",
            task,
        )
        self.assertIn(
            "timeout {{.DEPENDENCY_COMMAND_TIMEOUT}}\n"
            "        uv run pre-commit --version",
            task,
        )
        self.assertIn(
            "timeout {{.DEPENDENCY_AUTH_TIMEOUT}} python3\n"
            "        .github/scripts/update_dependencies.py check",
            task,
        )

    def test_github_action_upgrade_reports_authentication_failures(self) -> None:
        task_binary = shutil.which("go-task") or shutil.which("task")
        shell_binary = shutil.which("sh")
        timeout_binary = shutil.which("timeout")
        self.assertIsNotNone(task_binary)
        self.assertIsNotNone(shell_binary)
        self.assertIsNotNone(timeout_binary)
        expected = (
            "GitHub authentication is required; export PINACT_GITHUB_TOKEN or "
            "GITHUB_TOKEN, or authenticate the gh CLI."
        )

        with tempfile.TemporaryDirectory() as directory:
            binary_directory = Path(directory)
            (binary_directory / "sh").symlink_to(shell_binary)
            environment = os.environ.copy()
            environment["PATH"] = str(binary_directory)
            environment.pop("PINACT_GITHUB_TOKEN", None)
            environment.pop("GITHUB_TOKEN", None)

            missing_gh = subprocess.run(
                (task_binary, "--silent", "deps-upgrade:github-actions"),
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            (binary_directory / "timeout").symlink_to(timeout_binary)
            fake_gh = binary_directory / "gh"
            fake_gh.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            fake_gh.chmod(0o755)
            failed_gh = subprocess.run(
                (task_binary, "--silent", "deps-upgrade:github-actions"),
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

        for name, completed in (("missing", missing_gh), ("failed", failed_gh)):
            with self.subTest(name=name):
                output = completed.stdout + completed.stderr
                self.assertNotEqual(0, completed.returncode)
                self.assertIn(expected, output)
                self.assertNotIn("command not found", output)

    def test_shared_python_sync_is_portable_and_upgrade_sync_is_bounded(self) -> None:
        task = _task_block(self.taskfile, "deps-python")
        upgrade_task = _task_block(self.taskfile, "deps-upgrade:python")

        self.assertIn("uv sync --locked", task)
        self.assertNotIn("timeout", task)
        self.assertIn("timeout {{.DEPENDENCY_COMMAND_TIMEOUT}}", upgrade_task)

    def test_pre_commit_is_managed_by_the_project_environment(self) -> None:
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        verify = _task_block(self.taskfile, "deps-verify")

        self.assertIsNotNone(re.search(r'^    "pre-commit",$', project, re.MULTILINE))
        self.assertIn("deps: [deps-python]", verify)
        self.assertIn("uv run pre-commit --version", verify)

    def test_neovim_upgrade_uses_an_isolated_workspace(self) -> None:
        task = _task_block(self.taskfile, "deps-upgrade:nvim")

        for required in (
            'workspace="$(mktemp -d)"',
            "HOME=",
            "XDG_CONFIG_HOME=",
            "XDG_DATA_HOME=",
            "XDG_STATE_HOME=",
            "XDG_CACHE_HOME=",
            "NVIM_USE_MASON=auto",
            "NVIM_APPNAME=nvim",
            "NVIM_DOTFILES_DISABLE_PLUGINS=0",
            ".github/scripts/update_nvim.lua",
            "timeout 300s nvim --headless",
            "dotfiles/.config/nvim/lazy-lock.json",
        ):
            with self.subTest(required=required):
                self.assertIn(required, task)

    def test_github_actions_upgrade_uses_pinned_pinact(self) -> None:
        task = _task_block(self.taskfile, "deps-upgrade:github-actions")

        for required in (
            "PINACT_GITHUB_TOKEN:-${GITHUB_TOKEN:-}",
            'github_token="$(timeout {{.DEPENDENCY_AUTH_TIMEOUT}} '
            'gh auth token --hostname github.com 2>/dev/null)"',
            'PINACT_GITHUB_TOKEN="${github_token}"',
            "pinact@{{.PINACT_VERSION}}",
            "--update",
            "--verify-comment",
        ):
            with self.subTest(required=required):
                self.assertIn(required, task)
        self.assertNotIn("pinact@latest", task)

    def test_script_tasks_cover_npm_and_repository_pins(self) -> None:
        self.assertIn(
            "update_dependencies.py npm",
            _task_block(self.taskfile, "deps-upgrade:npm"),
        )
        self.assertIn(
            "update_dependencies.py repository",
            _task_block(self.taskfile, "deps-upgrade:repository"),
        )

    def test_renovate_does_not_update_its_version_without_node_engine(self) -> None:
        renovate_version_managers = [
            manager
            for manager in self.renovate["customManagers"]
            if "RENOVATE_VERSION" in "\n".join(manager.get("matchStrings", []))
        ]

        self.assertEqual([], renovate_version_managers)

    def test_renovate_ignores_fixtures_and_uses_public_galaxy(self) -> None:
        self.assertIn(".test/**", self.renovate["ignorePaths"])
        self.assertFalse(
            any(
                ".test/**" in rule.get("matchFileNames", [])
                for rule in self.renovate["packageRules"]
            )
        )
        rules = [
            rule
            for rule in self.renovate["packageRules"]
            if rule.get("matchManagers") == ["ansible-galaxy"]
        ]

        self.assertEqual(1, len(rules))
        self.assertEqual(
            ["https://galaxy.ansible.com/api/"],
            rules[0]["registryUrls"],
        )

    def test_renovate_prs_are_disabled_and_local_reports_opt_in(self) -> None:
        self.assertIs(self.renovate["enabled"], False)
        self.assertIn(
            "--enabled=true", _task_block(self.taskfile, "deps-report:github-actions")
        )


class GitHubActionsPinInventoryTest(unittest.TestCase):
    """Keep every remote workflow dependency reviewable and immutable."""

    USES_PATTERN = re.compile(
        r"^\s*(?:-\s*)?uses:\s*(?P<target>[^\s@]+)@(?P<ref>[^\s#]+)"
        r"(?:\s+#\s*(?P<comment>.+))?$"
    )
    SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
    VERSION_COMMENT_PATTERN = re.compile(r"v\d+(?:\.\d+){0,2}")

    def test_remote_actions_have_full_sha_and_update_comment(self) -> None:
        problems: list[str] = []
        remote_uses = 0
        workflow_paths = sorted(
            [
                *(ROOT / ".github/workflows").glob("*.y*ml"),
                *(ROOT / ".github/actions").rglob("action.y*ml"),
            ]
        )

        for path in workflow_paths:
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if re.match(r"^\s*(?:-\s*)?uses:", line) is None or re.search(
                    r"uses:\s*\./", line
                ):
                    continue
                remote_uses += 1
                match = self.USES_PATTERN.fullmatch(line)
                location = f"{path.relative_to(ROOT)}:{line_number}"
                if match is None:
                    problems.append(f"{location}: cannot parse remote uses reference")
                    continue
                if self.SHA_PATTERN.fullmatch(match.group("ref")) is None:
                    problems.append(f"{location}: ref is not a full lowercase SHA")
                comment = match.group("comment") or ""
                if self.VERSION_COMMENT_PATTERN.fullmatch(comment) is None:
                    problems.append(f"{location}: update comment is missing or invalid")

        self.assertGreater(remote_uses, 0, "no remote GitHub Actions references found")
        self.assertEqual([], problems)


if __name__ == "__main__":
    unittest.main()
