# Dependency Updates

The repository owns one weekly maintenance PR, scheduled for Monday at 04:23 UTC. The workflow in
`.github/workflows/dependencies.yml` runs the same `go-task deps-upgrade` command
used locally, then opens or updates `chore/weekly-dependencies`. An unmerged PR
is refreshed on the next run instead of creating another PR. Updates are
reviewed and pass normal PR checks; the workflow does not enable automerge.

Renovate PR creation is disabled in `renovate.json`. Its native lock-file
maintenance cannot join ordinary dependency updates, and Neovim needs its
native plugin manager. Running both producers would recreate the fragmented
queue. The pinned Renovate CLI remains available for read-only extraction via
`go-task deps-report:github-actions`; this command explicitly enables only its
local dry run. Existing remote Renovate PRs are not closed by a local edit.

## Coverage

| Surface | Weekly refresh |
| --- | --- |
| Python tools | `uv lock --upgrade`; `pyproject.toml` stays unpinned and `uv.lock` records resolved versions. |
| Ansible collections | Latest stable Galaxy releases in `requirements.yml`. |
| npm packages | Exact direct versions and transitive locks for managed Codex/MCP packages and `.github/tools/`. Lifecycle scripts are disabled. |
| Neovim plugins | Lazy updates every declared lock entry in a temporary HOME and XDG workspace. |
| Pre-commit hooks | Native `pre-commit autoupdate --freeze` records full commit SHAs and version comments; the updater normalizes frozen-comment spacing for Prettier. |
| GitHub Actions | Pinact updates version comments and full commit SHAs in workflows and local composite actions. |
| Repository tools | Renovate and its required Node minimum together, pinact, and the matching Super-Linter image tag. |
| CI bootstrap tools | Exact versions marked with GitHub release annotations in `.github/` YAML. |

The Neovim updater requires Neovim 0.11.3 or newer. It includes optional Mason
plugins without installing Mason tools, temporarily enables the legacy
EditorConfig plugin in the copied config, and fails on omitted pins or Lazy
task errors. Runtime enablement stays unchanged. The configured blink.cmp v1
compatibility line is retained; changing that policy is a separate migration.

Only stable releases are selected for release-based pins. Major upgrades are
included where the native updater supports them. A changed pinact Go module
major or an unsupported Renovate Node engine expression stops the refresh for
an explicit compatibility change; it is not silently ignored. A failed
refresh does not publish a partial PR.

OS package lists and AUR source URLs describe rolling packages, not locked
versions. Their package managers resolve versions when explicitly applied;
weekly Arch CI checks package availability against a fresh container. Python
and Node runtime majors are compatibility choices and need an explicit
migration. Vendored, locally customized agent skills also need an upstream
review; replacing them automatically would erase repository-specific rules.
Test fixtures and generated test workspaces are excluded from dependency
updates.

## Publication Setup

The scheduled workflow runs from the default branch after this configuration
is merged. Manual dispatch is restricted to that same trusted branch. Running
`go-task deps-upgrade` locally only changes files; it never commits or pushes.

Install a dedicated GitHub App on this repository with these repository
permissions:

- Contents: read and write.
- Pull requests: read and write.
- Workflows: read and write, to refresh action pins in workflow files.

Set the repository variable `DEPENDENCIES_APP_CLIENT_ID` to the App client ID
and the Actions secret `DEPENDENCIES_APP_PRIVATE_KEY` to its private key.
Keep the private key only in GitHub Actions secrets.
The App installation is limited to this repository; tokens are short-lived and
revoked after use. A normal `GITHUB_TOKEN` is used only for read-only update
lookups. It cannot substitute for the App token because PR events it creates
would not trigger the normal CI checks.

Dependency resolution and publication run on separate runners. The first can
execute downloaded tools and Neovim plugins but receives no write credential.
It uploads only the dependency patch. The publication job checks out the same
trusted revision and accepts only existing, regular dependency files. In CI
workflow and composite-action files, only action digests, their version comments,
and annotated bootstrap versions may change; triggers, permissions, commands,
and action repository paths must remain identical. The job applies the patch
without executing updated repository code, then creates the PR using the App
token.

## Extending Coverage

Put npm automation tools beneath `.github/tools/` with a committed lockfile.
For a CI bootstrap tool released on GitHub, annotate its exact version:

```yaml
# renovate: datasource=github-releases depName=astral-sh/uv
version: "0.12.21"
```

The annotation is understood by the repository updater and Renovate's
read-only extraction configuration. Add a genuinely new ecosystem to the
existing upgrade task and its publication path allowance; do not add another
scheduled PR producer. Keep coupled versions in one updater transaction.

## Upstream References

- [Renovate grouping limitations](https://docs.renovatebot.com/configuration-options/#groupname)
- [GitHub workflow trigger restrictions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
