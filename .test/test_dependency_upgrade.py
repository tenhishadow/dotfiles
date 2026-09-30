"""Network-free behavior tests for repository dependency upgrades."""

# Unit tests cover private authentication and atomic-write failure boundaries.
# pylint: disable=protected-access

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

import update_dependencies


def test_frozen_hook_spacing_preserves_other_content_and_is_idempotent(
    tmp_path, monkeypatch
):
    path = tmp_path / ".pre-commit-config.yaml"
    original = (
        "repos:\n  - repo: https://example.com/hooks\n"
        f"    rev: {'a' * 40}  # frozen: v1.2.3\n"
        "    hooks: [{id: example}]\n"
        "  # Preserve  # frozen: unrelated comments.\n"
        "  - repo: local\n"
        "    description: text  # frozen: unrelated content\n"
    )
    path.write_text(original, encoding="utf-8")
    native_update = mock.Mock()
    monkeypatch.setattr(update_dependencies.subprocess, "run", native_update)

    update_dependencies.update_pre_commit(tmp_path)
    formatted = path.read_bytes()
    update_dependencies.update_pre_commit(tmp_path)

    assert formatted.decode() == original.replace(
        f"{'a' * 40}  # frozen:", f"{'a' * 40} # frozen:"
    )
    assert path.read_bytes() == formatted
    assert (
        native_update.call_args_list
        == [
            mock.call(
                (sys.executable, "-m", "pre_commit", "autoupdate", "--freeze"),
                check=True,
                cwd=tmp_path,
                timeout=update_dependencies.PACKAGE_COMMAND_TIMEOUT_SECONDS,
            )
        ]
        * 2
    )


def test_failed_native_hook_update_is_reported_before_normalizing(
    tmp_path, monkeypatch, capsys, run_command
):
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    run_command(["git", "init", "--quiet", str(tmp_path)], check=True)
    path = tmp_path / ".pre-commit-config.yaml"
    original = f"repos: invalid\nrev: {'a' * 40}  # frozen: v1.2.3\n"
    path.write_text(original, encoding="utf-8")

    assert (
        update_dependencies.main(("--root", str(tmp_path), "pre-commit")) == 1
    )

    assert "dependency update failed:" in capsys.readouterr().err
    assert path.read_text() == original


def test_replaces_one_taskfile_scalar_without_reformatting():
    content = (
        'vars:\n  RENOVATE_VERSION: "44.48.3"\n'
        '  RENOVATE_NODE_MIN_VERSION: "24.11.0"\n'
    )
    assert update_dependencies.replace_taskfile_scalar(
        content, "RENOVATE_VERSION", "44.50.1"
    ) == content.replace('"44.48.3"', '"44.50.1"')


@pytest.mark.parametrize(
    "content",
    [
        'vars:\n  OTHER_VERSION: "1.0.0"\n',
        'vars:\n  RENOVATE_VERSION: "44.48.3"\n  RENOVATE_VERSION: "44.49.1"\n',
    ],
    ids=["missing", "duplicate"],
)
def test_rejects_ambiguous_taskfile_scalar(content):
    with pytest.raises(
        update_dependencies.DependencyUpdateError, match="expected exactly one"
    ):
        update_dependencies.replace_taskfile_scalar(
            content, "RENOVATE_VERSION", "44.50.1"
        )


@pytest.mark.parametrize(
    ("engine", "expected"),
    [
        ("^24.11.0", "24.11.0"),
        (">=24", None),
        ("24.x", None),
        ("^24.11.0 || ^26.0.0", None),
        ("*", None),
    ],
)
def test_node_engine_requires_a_precise_minimum(engine, expected):
    if expected is None:
        with pytest.raises(
            update_dependencies.DependencyUpdateError,
            match=r"unsupported.*engine",
        ):
            update_dependencies.parse_node_engine_minimum(engine)
    else:
        assert update_dependencies.parse_node_engine_minimum(engine) == expected


def test_gh_token_lookup_is_bounded_and_scoped_to_github_com(monkeypatch):
    run = mock.Mock(return_value=mock.Mock(stdout="token\n"))
    monkeypatch.setattr(update_dependencies.subprocess, "run", run)

    assert update_dependencies._gh_auth_token() == "token\n"

    run.assert_called_once_with(
        ("gh", "auth", "token", "--hostname", "github.com"),
        check=True,
        capture_output=True,
        text=True,
        timeout=update_dependencies.SHORT_COMMAND_TIMEOUT_SECONDS,
    )


@pytest.mark.parametrize(
    ("environment", "expected", "uses_loader"),
    [
        (
            {
                "PINACT_GITHUB_TOKEN": "pinact-token",
                "GITHUB_TOKEN": "github-token",
            },
            "pinact-token",
            False,
        ),
        ({"GITHUB_TOKEN": "github-token"}, "github-token", False),
        ({}, "gh-token", True),
    ],
    ids=["pinact-token", "github-token", "gh-fallback"],
)
def test_github_token_precedence(environment, expected, uses_loader):
    loader = mock.Mock(return_value=" gh-token\n")

    assert (
        update_dependencies.resolve_github_token(environment, loader)
        == expected
    )
    assert loader.call_count == int(uses_loader)


@pytest.mark.parametrize("failure", [FileNotFoundError("gh"), ""])
def test_missing_authentication_fails_closed(failure):
    loader = (
        mock.Mock(side_effect=failure)
        if isinstance(failure, Exception)
        else mock.Mock(return_value=failure)
    )
    with pytest.raises(
        update_dependencies.DependencyUpdateError,
        match="GitHub authentication is required",
    ):
        update_dependencies.resolve_github_token({}, loader)


@pytest.mark.parametrize("remaining", [42, 0, None, True])
def test_authentication_requires_valid_core_quota(remaining, monkeypatch):
    fetch = mock.Mock(
        return_value={"resources": {"core": {"remaining": remaining}}}
    )
    monkeypatch.setattr(update_dependencies, "_fetch_json", fetch)
    loader = mock.Mock(side_effect=AssertionError("environment token expected"))

    if remaining == 42:
        assert (
            update_dependencies.validate_github_authentication(
                {"GITHUB_TOKEN": "secret"}, loader
            )
            == "secret"
        )
    else:
        with pytest.raises(update_dependencies.DependencyUpdateError):
            update_dependencies.validate_github_authentication(
                {"GITHUB_TOKEN": "secret"}, loader
            )
    fetch.assert_called_once_with(
        "https://api.github.com/rate_limit", github_token="secret"
    )
    loader.assert_not_called()


@pytest.mark.parametrize("pinact_tag", ["v5.0.0", "v6.0.0"])
def test_repository_resolution_rejects_unsupported_pinact_major(
    pinact_tag, monkeypatch
):
    def fetch_json(url, **_kwargs):
        if url.endswith("/renovate/latest"):
            return {"version": "44.50.1", "engines": {"node": "^24.11.0"}}
        return {"tag_name": pinact_tag if "/pinact/" in url else "v8.7.0"}

    monkeypatch.setattr(update_dependencies, "_fetch_json", fetch_json)
    if pinact_tag == "v5.0.0":
        assert (
            update_dependencies._resolve_repository_pins("secret").pinact
            == pinact_tag
        )
    else:
        with pytest.raises(
            update_dependencies.DependencyUpdateError,
            match="pinact major changed",
        ):
            update_dependencies._resolve_repository_pins("secret")


def test_ansible_updates_preserve_comments_quotes_and_field_order():
    content = """collections:
  # Keep this comment and field order.
  - name: ansible.posix
    version: "2.1.0"  # exact pin
    source: https://galaxy.ansible.com
  - name: community.general
    version: '13.2.0'
    source: https://galaxy.ansible.com
"""
    assert update_dependencies.update_ansible_requirements(
        content, {"ansible.posix": "2.2.2", "community.general": "13.3.0"}
    ) == content.replace('"2.1.0"', '"2.2.2"').replace("'13.2.0'", "'13.3.0'")


@pytest.mark.parametrize(
    "names",
    [("unrelated.collection",), ("ansible.posix", "ansible.posix")],
    ids=["missing", "duplicate"],
)
def test_ansible_updates_reject_nonunique_collections(names):
    content = "collections:\n" + "".join(
        f'  - name: {name}\n    version: "2.1.0"\n' for name in names
    )
    with pytest.raises(update_dependencies.DependencyUpdateError):
        update_dependencies.update_ansible_requirements(
            content, {"ansible.posix": "2.2.2"}
        )


def test_galaxy_follows_relative_pagination_and_compares_versions(monkeypatch):
    next_link = "/api/v3/next"
    fetch = mock.Mock(
        side_effect=[
            {"data": [{"version": "9.9.0"}], "links": {"next": next_link}},
            {"data": [{"version": "10.0.0"}], "links": {"next": None}},
        ]
    )
    monkeypatch.setattr(update_dependencies, "_fetch_json", fetch)

    assert (
        update_dependencies._latest_collection_version("community.general")
        == "10.0.0"
    )
    assert fetch.call_count == 2
    assert fetch.call_args_list[1].args[0] == (
        f"https://galaxy.ansible.com{next_link}"
    )


def test_galaxy_pagination_is_bounded(monkeypatch):
    fetch = mock.Mock(
        return_value={
            "data": [{"version": "1.0.0"}],
            "links": {"next": "/api/v3/next"},
        }
    )
    monkeypatch.setattr(update_dependencies, "_fetch_json", fetch)

    with pytest.raises(
        update_dependencies.DependencyUpdateError, match=r"exceeds .* pages"
    ):
        update_dependencies._latest_collection_version("example.collection")

    assert fetch.call_count == update_dependencies.GALAXY_VERSION_MAX_PAGES


def _write_package(root, relative, content="{}\n"):
    package = root / relative
    package.mkdir(parents=True)
    (package / "package.json").write_text(content, encoding="utf-8")
    (package / "package-lock.json").write_text("{}\n", encoding="utf-8")
    return package


@pytest.mark.parametrize(
    "manifest", [{}, {"dependencies": []}, {"dependencies": {}}]
)
def test_npm_rejects_missing_or_invalid_dependency_maps(manifest):
    with pytest.raises(update_dependencies.DependencyUpdateError):
        update_dependencies.direct_npm_dependencies(manifest)


def test_npm_discovery_excludes_language_fixtures(tmp_path):
    managed = _write_package(
        tmp_path, update_dependencies.NPM_MANIFEST_ROOTS[0] / "locked-package"
    )
    _write_package(tmp_path, Path(".test/nvim/typescript"))

    assert update_dependencies._managed_npm_manifests(tmp_path) == (
        managed / "package.json",
    )


def test_malformed_manifest_has_a_cli_error_without_traceback(tmp_path, capsys):
    _write_package(
        tmp_path, update_dependencies.NPM_MANIFEST_ROOTS[0], "{invalid json}\n"
    )

    assert update_dependencies.main(("--root", str(tmp_path), "npm")) == 1

    error = capsys.readouterr().err
    assert "dependency update failed:" in error
    assert "Traceback" not in error


def test_npm_refreshes_sorted_direct_dependencies_then_transitive_locks(
    tmp_path, monkeypatch
):
    package = _write_package(
        tmp_path,
        update_dependencies.NPM_MANIFEST_ROOTS[0],
        json.dumps(
            {
                "dependencies": {
                    "zeta": "1.0.0",
                    "@scope/tool": "2.0.0",
                    "alpha": "3.0.0",
                }
            }
        ),
    )
    run = mock.Mock()
    monkeypatch.setattr(update_dependencies.subprocess, "run", run)

    update_dependencies.update_npm(tmp_path)

    assert run.call_count == 2
    install, update = [call.args[0] for call in run.call_args_list]
    assert install[:2] == ("npm", "install")
    assert install[-3:] == ("@scope/tool@latest", "alpha@latest", "zeta@latest")
    assert "--save-exact" in install
    assert update[:2] == ("npm", "update")
    for call in run.call_args_list:
        command = call.args[0]
        for flag in (
            "--package-lock-only",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--registry=https://registry.npmjs.org/",
        ):
            assert flag in command
        assert command[command.index("--prefix") + 1] == str(package)
        assert call.kwargs == {
            "check": True,
            "cwd": tmp_path,
            "timeout": update_dependencies.PACKAGE_COMMAND_TIMEOUT_SECONDS,
        }


@pytest.fixture(name="pin_files")
def _pin_files(tmp_path, monkeypatch):
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        'vars:\n  RENOVATE_VERSION: "44.48.3"\n'
        '  RENOVATE_NODE_MIN_VERSION: "22.13.0"\n'
        '  PINACT_VERSION: "v5.0.0"\n'
        '  SUPERLINTER_IMAGE_TAG: "slim-v8.6.0"\n',
        encoding="utf-8",
    )
    action = tmp_path / ".github/actions/setup/action.yml"
    action.parent.mkdir(parents=True)
    action.write_text(
        "steps:\n  - with:\n"
        "      # renovate: datasource=github-releases depName=astral-sh/uv\n"
        '      version: "0.12.0"\n'
        '  - with:\n      version: "3.14"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        update_dependencies,
        "validate_github_authentication",
        mock.Mock(return_value="secret"),
    )
    monkeypatch.setattr(
        update_dependencies,
        "_resolve_repository_pins",
        mock.Mock(
            return_value=update_dependencies.RepositoryPins(
                renovate="44.50.1",
                renovate_node_minimum="24.11.0",
                pinact="v5.0.1",
                super_linter="slim-v8.7.0",
            )
        ),
    )
    return taskfile, action


def test_coupled_pin_updates_are_idempotent_and_leave_unannotated_versions(
    tmp_path, pin_files, monkeypatch
):
    release = mock.Mock(return_value="0.12.21")
    monkeypatch.setattr(update_dependencies, "_latest_github_release", release)

    update_dependencies.update_repository_pins(tmp_path)
    first = tuple(path.read_bytes() for path in pin_files)
    update_dependencies.update_repository_pins(tmp_path)

    assert tuple(path.read_bytes() for path in pin_files) == first
    assert first[0] == (
        b'vars:\n  RENOVATE_VERSION: "44.50.1"\n'
        b'  RENOVATE_NODE_MIN_VERSION: "24.11.0"\n'
        b'  PINACT_VERSION: "v5.0.1"\n'
        b'  SUPERLINTER_IMAGE_TAG: "slim-v8.7.0"\n'
    )
    assert b'version: "0.12.21"' in first[1]
    assert b'version: "3.14"' in first[1]
    assert release.call_args_list == [mock.call("astral-sh/uv", "secret")] * 2


def test_resolution_failure_does_not_write(tmp_path, pin_files, monkeypatch):
    original = tuple(path.read_bytes() for path in pin_files)
    monkeypatch.setattr(
        update_dependencies,
        "_latest_github_release",
        mock.Mock(side_effect=ValueError("resolution failed")),
    )

    with pytest.raises(ValueError, match="resolution failed"):
        update_dependencies.update_repository_pins(tmp_path)

    assert tuple(path.read_bytes() for path in pin_files) == original


def test_atomic_write_preserves_mode_and_cleans_temporary_file(tmp_path):
    path = tmp_path / "Taskfile.yml"
    path.write_text("old\n", encoding="utf-8")
    path.chmod(0o640)
    with mock.patch.object(
        update_dependencies.os, "replace", wraps=os.replace
    ) as replace:
        update_dependencies._write_if_changed(path, "old\n", "new\n")

    assert path.read_text(encoding="utf-8") == "new\n"
    assert path.stat().st_mode & 0o777 == 0o640
    replace.assert_called_once()
    source, destination = replace.call_args.args
    assert Path(source).parent == path.parent
    assert destination == path
    assert list(tmp_path.iterdir()) == [path]


def test_failed_replace_preserves_original_and_cleans_temporary_file(
    tmp_path, monkeypatch
):
    path = tmp_path / "Taskfile.yml"
    path.write_text("old\n", encoding="utf-8")
    monkeypatch.setattr(
        update_dependencies.os,
        "replace",
        mock.Mock(side_effect=OSError("replace failed")),
    )

    with pytest.raises(OSError, match="replace failed"):
        update_dependencies._write_if_changed(path, "old\n", "new\n")

    assert path.read_text(encoding="utf-8") == "old\n"
    assert list(tmp_path.iterdir()) == [path]


def test_renovate_preserves_single_writer_and_fixture_boundaries(repo_root):
    config = json.loads((repo_root / "renovate.json").read_text())
    assert config["enabled"] is False
    assert ".test/**" in config["ignorePaths"]
    assert not any(
        ".test/**" in rule.get("matchFileNames", [])
        for rule in config["packageRules"]
    )
    galaxy = [
        rule
        for rule in config["packageRules"]
        if rule.get("matchManagers") == ["ansible-galaxy"]
    ]
    assert len(galaxy) == 1
    assert galaxy[0]["registryUrls"] == ["https://galaxy.ansible.com/api/"]
    assert not any(
        "RENOVATE_VERSION" in "\n".join(manager.get("matchStrings", []))
        for manager in config["customManagers"]
    )


def test_remote_actions_have_immutable_pins_and_update_comments(repo_root):
    paths = sorted(
        [
            *(repo_root / ".github/workflows").glob("*.y*ml"),
            *(repo_root / ".github/actions").rglob("action.y*ml"),
        ]
    )
    references = []
    for path in paths:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not re.match(r"^\s*(?:-\s*)?uses:", line):
                continue
            if re.search(r"uses:\s*(?:\./|\$/)", line):
                continue
            location = f"{path.relative_to(repo_root)}:{number}"
            assert re.fullmatch(
                r"\s*(?:-\s*)?uses:\s*[^\s@]+@[0-9a-f]{40}\s+#\s+"
                r"v\d+(?:\.\d+){0,2}",
                line,
            ), location
            references.append(location)
    assert references, "No remote GitHub Actions references found"
