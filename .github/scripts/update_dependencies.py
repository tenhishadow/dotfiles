#!/usr/bin/env python3
"""Update repository dependency pins that have no suitable native updater."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HTTP_TIMEOUT_SECONDS = 30
SHORT_COMMAND_TIMEOUT_SECONDS = 30
PACKAGE_COMMAND_TIMEOUT_SECONDS = 600
GITHUB_RELEASE_PAGE_SIZE = 100
GITHUB_RELEASE_MAX_PAGES = 100
USER_AGENT = "tenhishadow-dotfiles-dependency-updater"
NPM_MANIFEST_ROOTS = (
    Path("dotfiles/.local/share/codex-cli"),
    Path("dotfiles/.local/share/codex-mcp"),
)
GITHUB_RELEASES = {
    "pinact": "suzuki-shunsuke/pinact",
    "super-linter": "super-linter/super-linter",
}

_PACKAGE_NAME_RE = re.compile(
    r"^(?:@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*$",
    re.IGNORECASE,
)
_SEMVER_RE = re.compile(r"^(?:v)?(?P<version>\d+\.\d+\.\d+)$")
_COLLECTION_NAME_RE = re.compile(
    r"^[ \t]*-[ \t]+name:[ \t]+(?P<name>[A-Za-z0-9_]+\.[A-Za-z0-9_]+)"
    r"[ \t]*(?:#.*)?$"
)
_COLLECTION_VERSION_RE = re.compile(
    r"^(?P<prefix>[ \t]*version:[ \t]*)"
    r"(?P<quote>['\"]?)(?P<version>[^'\"# \t]+)(?P=quote)"
    r"(?P<suffix>[ \t]*(?:#.*)?)$"
)
_COLLECTION_SOURCE_RE = re.compile(
    r"^[ \t]*source:[ \t]*(?P<source>\S+)[ \t]*(?:#.*)?$"
)
_REUSABLE_WORKFLOW_RE = re.compile(
    r"uses:[ \t]+"
    r"(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/"
    r"(?P<workflow>[^@ \t\r\n]+)@"
    r"(?P<sha>[a-f0-9]{40})"
    r"[ \t]+#[ \t]+renovate:[ \t]+branch="
    r"(?P<branch>[A-Za-z0-9._/-]+)"
)


class DependencyUpdateError(ValueError):
    """Raised when an update cannot be applied without ambiguity."""


@dataclass(frozen=True)
class CollectionRequirement:
    """An Ansible Galaxy collection declared in requirements.yml."""

    name: str
    source: str


@dataclass(frozen=True)
class RepositoryPins:
    """Resolved versions stored directly in Taskfile.yml."""

    renovate: str
    renovate_node_minimum: str
    pinact: str
    super_linter: str


def replace_taskfile_scalar(text: str, name: str, value: str) -> str:
    """Replace one quoted top-level Taskfile variable, rejecting ambiguity."""

    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
        raise DependencyUpdateError(f"invalid Taskfile variable name: {name!r}")
    pattern = re.compile(
        rf'^(?P<prefix>[ ]{{2}}{re.escape(name)}:[ \t]*")[^"\r\n]+'
        r'(?P<suffix>"[ \t]*)$',
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise DependencyUpdateError(
            f"expected exactly one {name} assignment, found {len(matches)}"
        )
    return pattern.sub(
        lambda match: f"{match.group('prefix')}{value}{match.group('suffix')}",
        text,
    )


def parse_node_engine_minimum(engine: str) -> str:
    """Return the minimum version from Renovate's supported caret constraint."""

    match = re.fullmatch(r"\^(\d+\.\d+\.\d+)", engine.strip())
    if not match:
        raise DependencyUpdateError(
            f"unsupported Renovate Node.js engine constraint: {engine!r}"
        )
    return match.group(1)


def resolve_github_token(
    environ: Mapping[str, str], gh_token_loader: Callable[[], str]
) -> str:
    """Resolve a GitHub token without printing or persisting its value."""

    for name in ("PINACT_GITHUB_TOKEN", "GITHUB_TOKEN"):
        token = environ.get(name, "").strip()
        if token:
            return token
    try:
        token = gh_token_loader().strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise DependencyUpdateError(
            "GitHub authentication is required; export PINACT_GITHUB_TOKEN or "
            "GITHUB_TOKEN, or authenticate the gh CLI"
        ) from error
    if not token:
        raise DependencyUpdateError(
            "GitHub authentication is required; export PINACT_GITHUB_TOKEN or "
            "GITHUB_TOKEN, or authenticate the gh CLI"
        )
    return token


def latest_stable_release_tag(
    payload: object, *, required_major: int | None = None
) -> str:
    """Select the highest stable semantic release, optionally within one major."""

    if not isinstance(payload, list):
        raise DependencyUpdateError("GitHub releases response must be a list")
    candidates: list[tuple[tuple[int, int, int], str]] = []
    for release in payload:
        if not isinstance(release, dict):
            continue
        if release.get("draft") is True or release.get("prerelease") is True:
            continue
        tag = release.get("tag_name")
        if not isinstance(tag, str):
            continue
        match = _SEMVER_RE.fullmatch(tag)
        if match is None:
            continue
        version = tuple(int(part) for part in match.group("version").split("."))
        if required_major is not None and version[0] != required_major:
            continue
        candidates.append((version, tag))
    if not candidates:
        major = "" if required_major is None else f" in major v{required_major}"
        raise DependencyUpdateError(
            f"GitHub returned no stable semantic releases{major}"
        )
    return max(candidates, key=lambda candidate: candidate[0])[1]


def _line_body_and_ending(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body) :]


def _collection_requirements(text: str) -> tuple[CollectionRequirement, ...]:
    requirements: list[CollectionRequirement] = []
    current_name: str | None = None
    current_source = "https://galaxy.ansible.com"

    def finish_current() -> None:
        if current_name is None:
            return
        requirements.append(CollectionRequirement(current_name, current_source))

    for line in text.splitlines():
        name_match = _COLLECTION_NAME_RE.fullmatch(line)
        if name_match:
            finish_current()
            current_name = name_match.group("name")
            current_source = "https://galaxy.ansible.com"
            continue
        source_match = _COLLECTION_SOURCE_RE.fullmatch(line)
        if source_match and current_name is not None:
            current_source = source_match.group("source")
    finish_current()

    names = [requirement.name for requirement in requirements]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise DependencyUpdateError(
            "duplicate Ansible collection requirements: " + ", ".join(duplicates)
        )
    if not requirements:
        raise DependencyUpdateError("no Ansible collection requirements found")
    unsupported = [
        requirement
        for requirement in requirements
        if requirement.source.rstrip("/") != "https://galaxy.ansible.com"
    ]
    if unsupported:
        rendered = ", ".join(
            f"{requirement.name} ({requirement.source})" for requirement in unsupported
        )
        raise DependencyUpdateError(
            f"unsupported Ansible collection source: {rendered}"
        )
    return tuple(requirements)


def update_ansible_requirements(text: str, versions: Mapping[str, str]) -> str:
    """Update collection versions while preserving the existing YAML layout."""

    if not versions:
        raise DependencyUpdateError("no Ansible collection updates were supplied")
    for name, version in versions.items():
        if not _COLLECTION_NAME_RE.fullmatch(f"- name: {name}"):
            raise DependencyUpdateError(f"invalid Ansible collection name: {name!r}")
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise DependencyUpdateError(
                f"invalid stable version for Ansible collection {name}: {version!r}"
            )

    current_name: str | None = None
    replacements = dict.fromkeys(versions, 0)
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        body, ending = _line_body_and_ending(line)
        name_match = _COLLECTION_NAME_RE.fullmatch(body)
        if name_match:
            current_name = name_match.group("name")
            output.append(line)
            continue
        version_match = _COLLECTION_VERSION_RE.fullmatch(body)
        if version_match and current_name in versions:
            replacements[current_name] += 1
            output.append(
                version_match.group("prefix")
                + version_match.group("quote")
                + versions[current_name]
                + version_match.group("quote")
                + version_match.group("suffix")
                + ending
            )
            continue
        output.append(line)

    invalid_counts = {name: count for name, count in replacements.items() if count != 1}
    if invalid_counts:
        details = ", ".join(
            f"{name}={count}" for name, count in sorted(invalid_counts.items())
        )
        raise DependencyUpdateError(
            f"expected exactly one version for each Ansible collection: {details}"
        )
    return "".join(output)


def replace_reusable_workflow_sha(
    text: str, repository: str, branch: str, sha: str
) -> str:
    """Replace one branch-tracked reusable workflow SHA."""

    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise DependencyUpdateError(f"invalid GitHub repository: {repository!r}")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise DependencyUpdateError(f"invalid Git branch: {branch!r}")
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise DependencyUpdateError(f"invalid Git commit SHA: {sha!r}")

    pattern = re.compile(
        r"(?P<prefix>uses:[ \t]+" + re.escape(repository) + r"/[^@ \t\r\n]+@)"
        r"[a-f0-9]{40}"
        r"(?P<suffix>[ \t]+#[ \t]+renovate:[ \t]+branch="
        + re.escape(branch)
        + r"(?:[ \t]*)(?=$|\r?\n))",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise DependencyUpdateError(
            "expected exactly one reusable workflow reference for "
            f"{repository}@{branch}, found {len(matches)}"
        )
    return pattern.sub(
        lambda match: f"{match.group('prefix')}{sha}{match.group('suffix')}",
        text,
    )


def direct_npm_dependencies(manifest: object) -> tuple[str, ...]:
    """Return every direct npm package name from supported dependency sections."""

    if not isinstance(manifest, dict):
        raise DependencyUpdateError("npm manifest root must be an object")
    dependencies: list[str] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        values = manifest.get(section, {})
        if not isinstance(values, dict):
            raise DependencyUpdateError(f"npm manifest {section} must be an object")
        for package in values:
            if not isinstance(package, str) or not _PACKAGE_NAME_RE.fullmatch(package):
                raise DependencyUpdateError(f"invalid npm package name: {package!r}")
            if package in dependencies:
                raise DependencyUpdateError(
                    f"npm package appears in multiple dependency sections: {package}"
                )
            dependencies.append(package)
    if not dependencies:
        raise DependencyUpdateError("npm manifest has no direct dependencies")
    return tuple(sorted(dependencies))


def build_npm_update_command(
    directory: Path | str,
    dependencies: Sequence[str],
    *,
    save_flag: str | None = None,
) -> tuple[str, ...]:
    """Build an npm lock-only update command without lifecycle scripts."""

    if not dependencies:
        raise DependencyUpdateError("cannot build an npm update with no packages")
    for package in dependencies:
        if not _PACKAGE_NAME_RE.fullmatch(package):
            raise DependencyUpdateError(f"invalid npm package name: {package!r}")
    command = [
        "npm",
        "install",
        "--package-lock-only",
        "--ignore-scripts",
        "--no-audit",
        "--no-fund",
        "--save-exact",
    ]
    if save_flag is not None:
        command.append(save_flag)
    command.extend(("--prefix", str(directory)))
    command.extend(f"{package}@latest" for package in dependencies)
    return tuple(command)


def _gh_auth_token() -> str:
    result = subprocess.run(
        ("gh", "auth", "token", "--hostname", "github.com"),
        check=True,
        capture_output=True,
        text=True,
        timeout=SHORT_COMMAND_TIMEOUT_SECONDS,
    )
    return result.stdout


def _fetch_json(url: str, *, github_token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json, application/json",
        "User-Agent": USER_AGENT,
    }
    if github_token and urllib.parse.urlparse(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {github_token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise DependencyUpdateError(f"failed to fetch {url}: {error}") from error


def validate_github_authentication(
    environ: Mapping[str, str], gh_token_loader: Callable[[], str]
) -> str:
    """Resolve and validate GitHub authentication before any repository writes."""

    token = resolve_github_token(environ, gh_token_loader)
    payload = _fetch_json(
        "https://api.github.com/rate_limit",
        github_token=token,
    )
    if not isinstance(payload, dict):
        raise DependencyUpdateError("invalid GitHub rate-limit response")
    resources = payload.get("resources")
    core = resources.get("core") if isinstance(resources, dict) else None
    remaining = core.get("remaining") if isinstance(core, dict) else None
    if isinstance(remaining, bool) or not isinstance(remaining, int):
        raise DependencyUpdateError("GitHub rate-limit response has no core quota")
    if remaining <= 0:
        raise DependencyUpdateError("GitHub API core rate limit is exhausted")
    return token


def _latest_collection_version(name: str) -> str:
    namespace, collection = name.split(".", maxsplit=1)
    url = (
        "https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/"
        f"collections/index/{namespace}/{collection}/versions/?limit=100"
    )
    payload = _fetch_json(url)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise DependencyUpdateError(f"invalid Galaxy response for {name}")
    stable_versions: list[tuple[tuple[int, int, int], str]] = []
    for entry in payload["data"]:
        if not isinstance(entry, dict):
            continue
        version = entry.get("version")
        if not isinstance(version, str):
            continue
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
        if match:
            stable_versions.append((tuple(map(int, match.groups())), version))
    if not stable_versions:
        raise DependencyUpdateError(f"Galaxy returned no stable versions for {name}")
    return max(stable_versions)[1]


def _latest_github_release(
    repository: str,
    github_token: str,
    *,
    required_major: int | None = None,
) -> str:
    if required_major is None:
        url = f"https://api.github.com/repos/{repository}/releases/latest"
        payload = _fetch_json(url, github_token=github_token)
        releases = [payload]
    else:
        releases = []
        for page in range(1, GITHUB_RELEASE_MAX_PAGES + 1):
            url = (
                f"https://api.github.com/repos/{repository}/releases"
                f"?per_page={GITHUB_RELEASE_PAGE_SIZE}&page={page}"
            )
            payload = _fetch_json(url, github_token=github_token)
            if not isinstance(payload, list):
                raise DependencyUpdateError(
                    f"invalid releases response for {repository}: expected a list"
                )
            releases.extend(payload)
            if len(payload) < GITHUB_RELEASE_PAGE_SIZE:
                break
        else:
            raise DependencyUpdateError(
                f"GitHub release history for {repository} exceeds "
                f"{GITHUB_RELEASE_MAX_PAGES} pages"
            )
    try:
        return latest_stable_release_tag(releases, required_major=required_major)
    except DependencyUpdateError as error:
        raise DependencyUpdateError(
            f"invalid releases response for {repository}: {error}"
        ) from error


def _resolve_repository_pins(github_token: str) -> RepositoryPins:
    urls: dict[str, Callable[[], Any]] = {
        "renovate": lambda: _fetch_json("https://registry.npmjs.org/renovate/latest"),
        "pinact": lambda: _latest_github_release(
            GITHUB_RELEASES["pinact"], github_token, required_major=4
        ),
        "super-linter": lambda: _latest_github_release(
            GITHUB_RELEASES["super-linter"], github_token
        ),
    }
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {name: executor.submit(resolver) for name, resolver in urls.items()}
        resolved = {name: future.result() for name, future in futures.items()}

    renovate_payload = resolved["renovate"]
    if not isinstance(renovate_payload, dict):
        raise DependencyUpdateError("invalid npm response for Renovate")
    renovate_version = renovate_payload.get("version")
    engines = renovate_payload.get("engines")
    if not isinstance(renovate_version, str) or not re.fullmatch(
        r"\d+\.\d+\.\d+", renovate_version
    ):
        raise DependencyUpdateError("npm returned an invalid Renovate version")
    if not isinstance(engines, dict) or not isinstance(engines.get("node"), str):
        raise DependencyUpdateError("npm returned no Renovate Node.js engine")

    pinact = resolved["pinact"]
    super_linter = resolved["super-linter"]
    if not isinstance(pinact, str) or not pinact.startswith("v4."):
        raise DependencyUpdateError(
            f"pinact major changed; update its Go module path manually: {pinact!r}"
        )
    if not isinstance(super_linter, str):
        raise DependencyUpdateError("invalid Super-Linter release")
    return RepositoryPins(
        renovate=renovate_version,
        renovate_node_minimum=parse_node_engine_minimum(engines["node"]),
        pinact=pinact,
        super_linter=f"slim-{super_linter}",
    )


def _resolve_git_branch(repository: str, branch: str) -> str:
    remote = f"https://github.com/{repository}.git"
    result = subprocess.run(
        ("git", "ls-remote", remote, f"refs/heads/{branch}"),
        check=True,
        capture_output=True,
        text=True,
        timeout=SHORT_COMMAND_TIMEOUT_SECONDS,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise DependencyUpdateError(
            f"expected one remote ref for {repository}@{branch}, found {len(lines)}"
        )
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != f"refs/heads/{branch}":
        raise DependencyUpdateError(
            f"unexpected remote ref response for {repository}@{branch}"
        )
    sha = fields[0]
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise DependencyUpdateError(
            f"invalid remote SHA for {repository}@{branch}: {sha!r}"
        )
    return sha


def _write_if_changed(path: Path, old: str, new: str) -> None:
    if new == old:
        print(f"up to date: {path}")
        return
    path.write_text(new, encoding="utf-8")
    print(f"updated: {path}")


def update_ansible(root: Path) -> None:
    """Resolve and write exact Galaxy versions, then install the lock surface."""

    path = root / "requirements.yml"
    original = path.read_text(encoding="utf-8")
    requirements = _collection_requirements(original)
    with ThreadPoolExecutor(max_workers=len(requirements)) as executor:
        futures = {
            requirement.name: executor.submit(
                _latest_collection_version, requirement.name
            )
            for requirement in requirements
        }
        versions = {name: future.result() for name, future in futures.items()}
    updated = update_ansible_requirements(original, versions)
    _write_if_changed(path, original, updated)


def _tracked_reusable_workflows(
    workflow_texts: Mapping[Path, str],
) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for text in workflow_texts.values():
        for match in _REUSABLE_WORKFLOW_RE.finditer(text):
            refs.add((match.group("repository"), match.group("branch")))
    return refs


def _update_workflow_refs(
    text: str, resolved_refs: Mapping[tuple[str, str], str]
) -> str:
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        match = _REUSABLE_WORKFLOW_RE.search(line)
        if not match:
            output.append(line)
            continue
        repository = match.group("repository")
        branch = match.group("branch")
        output.append(
            replace_reusable_workflow_sha(
                line, repository, branch, resolved_refs[(repository, branch)]
            )
        )
    return "".join(output)


def _resolve_workflow_refs(
    workflow_texts: Mapping[Path, str],
) -> dict[tuple[str, str], str]:
    refs = _tracked_reusable_workflows(workflow_texts)
    if not refs:
        return {}
    with ThreadPoolExecutor(max_workers=len(refs)) as executor:
        futures = {ref: executor.submit(_resolve_git_branch, *ref) for ref in refs}
        return {ref: future.result() for ref, future in futures.items()}


def _replace_repository_pins(text: str, pins: RepositoryPins) -> str:
    updated = text
    for name, value in (
        ("RENOVATE_VERSION", pins.renovate),
        ("RENOVATE_NODE_MIN_VERSION", pins.renovate_node_minimum),
        ("PINACT_VERSION", pins.pinact),
        ("SUPERLINTER_IMAGE_TAG", pins.super_linter),
    ):
        updated = replace_taskfile_scalar(updated, name, value)
    return updated


def update_repository_pins(root: Path) -> None:
    """Update Taskfile tool versions and branch-tracked reusable workflows."""

    taskfile_path = root / "Taskfile.yml"
    taskfile_original = taskfile_path.read_text(encoding="utf-8")
    workflows = tuple(sorted((root / ".github/workflows").glob("*.y*ml")))
    workflow_originals = {path: path.read_text(encoding="utf-8") for path in workflows}

    github_token = validate_github_authentication(os.environ, _gh_auth_token)
    taskfile_updated = _replace_repository_pins(
        taskfile_original, _resolve_repository_pins(github_token)
    )
    resolved_refs = _resolve_workflow_refs(workflow_originals)

    _write_if_changed(taskfile_path, taskfile_original, taskfile_updated)
    for path, original in workflow_originals.items():
        _write_if_changed(
            path, original, _update_workflow_refs(original, resolved_refs)
        )


def _managed_npm_manifests(root: Path) -> tuple[Path, ...]:
    manifests: list[Path] = []
    for relative_root in NPM_MANIFEST_ROOTS:
        base = root / relative_root
        for path in base.rglob("package.json"):
            if "node_modules" in path.relative_to(base).parts:
                continue
            if not path.with_name("package-lock.json").is_file():
                raise DependencyUpdateError(f"npm manifest has no package lock: {path}")
            manifests.append(path)
    if not manifests:
        raise DependencyUpdateError("no managed npm manifests found")
    return tuple(sorted(manifests))


def _npm_dependency_sections(
    manifest: object,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    direct_npm_dependencies(manifest)
    if not isinstance(manifest, dict):
        raise DependencyUpdateError("npm manifest root must be an object")
    sections: list[tuple[str, tuple[str, ...]]] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        values = manifest.get(section, {})
        if values:
            sections.append((section, tuple(sorted(values))))
    return tuple(sections)


def update_npm(root: Path) -> None:
    """Update every direct dependency in managed npm package locks."""

    save_flags = {
        "dependencies": None,
        "devDependencies": "--save-dev",
        "optionalDependencies": "--save-optional",
    }
    for manifest_path in _managed_npm_manifests(root):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sections = _npm_dependency_sections(manifest)
        if not sections:
            raise DependencyUpdateError(
                f"managed npm manifest has no direct dependencies: {manifest_path}"
            )
        for section, dependencies in sections:
            command = build_npm_update_command(
                manifest_path.parent,
                dependencies,
                save_flag=save_flags[section],
            )
            subprocess.run(
                command,
                check=True,
                cwd=root,
                timeout=PACKAGE_COMMAND_TIMEOUT_SECONDS,
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (defaults to the script checkout)",
    )
    parser.add_argument(
        "surface",
        choices=("check", "ansible", "npm", "repository"),
        help="dependency surface to update",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one dependency updater surface."""

    args = _parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.surface == "check":
            validate_github_authentication(os.environ, _gh_auth_token)
        elif args.surface == "ansible":
            update_ansible(root)
        elif args.surface == "npm":
            update_npm(root)
        else:
            update_repository_pins(root)
    except (
        DependencyUpdateError,
        json.JSONDecodeError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        print(f"dependency update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
