"""Contract tests for repository-managed Codex configuration and npm locks."""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODEX_DIR = ROOT / "dotfiles/.codex"
PONYTAIL_DIR = ROOT / "dotfiles/.agents/skills/ponytail"
PACKAGE_DIRS = (
    ROOT / "dotfiles/.local/share/codex-cli/locked",
    ROOT / "dotfiles/.local/share/codex-mcp/context7",
    ROOT / "dotfiles/.local/share/codex-mcp/playwright",
)
_MISSING = object()


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _direct_dependency_problems(
    dependencies: dict[str, object], packages: dict[str, object]
) -> list[str]:
    problems: list[str] = []
    root_package = packages.get("")
    if not isinstance(root_package, dict):
        problems.append("lock root package is missing")
    elif root_package.get("dependencies") != dependencies:
        problems.append("manifest dependencies differ from lock root")

    for dependency, expected_version in dependencies.items():
        locked_package = packages.get(f"node_modules/{dependency}")
        if not isinstance(locked_package, dict):
            problems.append(f"{dependency} is missing from lock packages")
        elif locked_package.get("version") != expected_version:
            problems.append(
                f"{dependency} resolves to {locked_package.get('version')!r}, "
                f"expected exact {expected_version!r}"
            )
    return problems


def _integrity_problems(packages: dict[str, object]) -> list[str]:
    problems: list[str] = []
    for package_path, package in packages.items():
        if package_path == "":
            continue
        if not isinstance(package, dict):
            problems.append(f"{package_path} lock entry is not an object")
            continue
        if package.get("link") is True:
            continue
        integrity = package.get("integrity")
        if not isinstance(integrity, str) or not integrity:
            problems.append(f"{package_path} has no integrity hash")
    return problems


def _package_lock_problems(manifest: object, lock: object) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest root is not an object"]
    if not isinstance(lock, dict):
        return ["lock root is not an object"]

    dependencies = manifest.get("dependencies")
    packages = lock.get("packages")
    if not isinstance(dependencies, dict):
        return ["manifest dependencies is not an object"]
    if not isinstance(packages, dict):
        return ["lock packages is not an object"]
    return _direct_dependency_problems(dependencies, packages) + _integrity_problems(
        packages
    )


def _valid_package_data() -> tuple[dict[str, object], dict[str, object]]:
    dependencies = {"example": "1.2.3"}
    return (
        {"dependencies": dependencies},
        {
            "packages": {
                "": {"dependencies": dependencies},
                "node_modules/example": {
                    "version": "1.2.3",
                    "resolved": "https://registry.example/example.tgz",
                    "integrity": "sha512-example",
                },
            }
        },
    )


def _change_nested(
    mapping: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    current = mapping
    for key in path[:-1]:
        child = current[key]
        if not isinstance(child, dict):
            raise TypeError(f"{key} is not an object")
        current = child
    if value is _MISSING:
        del current[path[-1]]
    else:
        current[path[-1]] = value


class AgentToolingContractTest(unittest.TestCase):
    """Validate the tracked Codex configuration and locked npm packages."""

    def test_managed_configs_parse_to_mappings(self) -> None:
        toml_paths = sorted(CODEX_DIR.glob("*.toml"))
        json_paths = sorted(CODEX_DIR.glob("*.json"))
        self.assertTrue(toml_paths, "no managed Codex TOML configuration found")
        self.assertTrue(json_paths, "no managed Codex JSON configuration found")

        for path in toml_paths:
            with self.subTest(path=path.relative_to(ROOT)), path.open("rb") as stream:
                self.assertIsInstance(tomllib.load(stream), dict)
        for path in json_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsInstance(_read_json(path), dict)

    def test_ponytail_is_explicit_only_and_does_not_limit_validation(self) -> None:
        skill = (PONYTAIL_DIR / "SKILL.md").read_text(encoding="utf-8")
        openai_config = (PONYTAIL_DIR / "agents/openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn('local_policy: "opt-in-lite"', skill)
        self.assertIn("does not cap the number or size of tests", skill)
        self.assertIn("allow_implicit_invocation: false", openai_config)
        self.assertIn("$ponytail", openai_config)

    def test_package_locks_match_manifests_and_have_integrity(self) -> None:
        for directory in PACKAGE_DIRS:
            with self.subTest(directory=directory.relative_to(ROOT)):
                manifest = _read_json(directory / "package.json")
                lock = _read_json(directory / "package-lock.json")
                self.assertEqual([], _package_lock_problems(manifest, lock))

    def test_package_lock_contract_rejects_invalid_inputs(self) -> None:
        cases: tuple[tuple[str, tuple[tuple[str, ...], object], str], ...] = (
            (
                "root drift",
                (("packages", "", "dependencies"), {}),
                "differ from lock root",
            ),
            (
                "missing package",
                (("packages", "node_modules/example"), _MISSING),
                "missing from lock",
            ),
            (
                "version drift",
                (("packages", "node_modules/example", "version"), "9.9.9"),
                "expected exact",
            ),
            (
                "missing integrity",
                (("packages", "node_modules/example", "integrity"), _MISSING),
                "no integrity",
            ),
            (
                "missing artifact metadata",
                (("packages", "node_modules/example"), {"version": "1.2.3"}),
                "no integrity",
            ),
            (
                "invalid package entry",
                (("packages", "node_modules/example"), None),
                "not an object",
            ),
        )
        for name, change, expected in cases:
            with self.subTest(name=name):
                manifest, lock = _valid_package_data()
                _change_nested(lock, *change)
                self.assertTrue(
                    any(
                        expected in problem
                        for problem in _package_lock_problems(manifest, lock)
                    )
                )


if __name__ == "__main__":
    unittest.main()
