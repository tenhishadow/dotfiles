"""Contract tests for repository-managed Codex configuration and npm locks."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
import yaml

PACKAGE_DIRS = (
    "dotfiles/.local/share/codex-cli/locked",
    "dotfiles/.local/share/codex-mcp/context7",
    "dotfiles/.local/share/codex-mcp/playwright",
)


@pytest.mark.parametrize("suffix", ["toml", "json"])
def test_managed_configs_parse_to_mappings(repo_root: Path, suffix):
    paths = sorted((repo_root / "dotfiles/.codex").glob(f"*.{suffix}"))
    assert paths, f"no managed Codex {suffix} configuration found"
    for path in paths:
        data = path.read_text(encoding="utf-8")
        parsed = tomllib.loads(data) if suffix == "toml" else json.loads(data)
        assert isinstance(parsed, dict), path.name


def test_ponytail_is_explicit_only(repo_root: Path):
    directory = repo_root / "dotfiles/.agents/skills/ponytail"
    metadata = yaml.safe_load(
        (directory / "SKILL.md").read_text().split("---", 2)[1]
    )
    config = yaml.safe_load((directory / "agents/openai.yaml").read_text())
    assert metadata["metadata"]["local_policy"] == "opt-in-lite"
    assert config["policy"]["allow_implicit_invocation"] is False
    assert "$ponytail" in config["interface"]["default_prompt"]


def test_ponytail_deploys_as_files_and_removes_the_legacy_directory_link(
    repo_root: Path,
):
    inventory = yaml.safe_load(
        (repo_root / "inventory/host_vars/this_host/dotfiles.yml").read_text()
    )
    payload = ".agents/skills/ponytail"
    destination = "{{ dotfiles_home }}/" + payload
    legacy = [
        link
        for link in inventory["dotfiles_legacy_directory_links"]
        if link["payload"] == payload
    ]
    assert [link["dest"] for link in legacy] == [destination]
    mappings = [
        (mapping["payload"], mapping["dest"])
        for mapping in inventory["dotfiles_mapping"]
        if mapping["payload"] == payload
        or mapping["payload"].startswith(payload + "/")
    ]
    assert sorted(mappings) == sorted(
        (f"{payload}/{name}", f"{destination}/{name}")
        for name in ("SKILL.md", "LICENSE", "agents/openai.yaml")
    )


@pytest.mark.parametrize("directory", PACKAGE_DIRS)
def test_package_locks_match_manifests_and_have_integrity(
    repo_root: Path, directory
):
    package_dir = repo_root / directory
    manifest = json.loads((package_dir / "package.json").read_text())
    lock = json.loads((package_dir / "package-lock.json").read_text())
    dependencies = manifest["dependencies"]
    packages = lock["packages"]
    assert isinstance(dependencies, dict)
    assert dependencies
    assert packages[""]["dependencies"] == dependencies
    for name, version in dependencies.items():
        assert packages[f"node_modules/{name}"]["version"] == version, name
    for path, package in packages.items():
        if not path or package.get("link") is True:
            continue
        integrity = package["integrity"]
        assert isinstance(integrity, str), path
        assert integrity, path
