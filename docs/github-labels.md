# GitHub Labels

This is the catalog of labels required by repository automation and issue
forms. `.github/labeler.yml` owns path matching;
`.github/workflows/labeler.yml` applies those labels. Labels classify work;
[Conventional Commit messages](../CONTRIBUTING.md#commits-and-pull-requests)
control release meaning.

## Pipeline

- The metadata-only workflow uses `pull_request_target` so fork PRs can receive
  labels. It never checks out or executes PR code; the pinned action reads the
  trusted repository configuration through the GitHub API.
- Permissions are limited to reading repository content and writing PR
  metadata. All required labels already exist; the workflow does not need
  `issues: write` to create them.
- `sync-labels: false` makes assignment additive, preserving existing manual,
  triage, and release labels. Remove an obsolete area label manually when
  necessary; automatic relabeling does not erase it.
- No artificial changed-file or new-label limit suppresses classification of
  broad maintenance PRs. Keep the small catalog below GitHub's PR label limit.

These boundaries follow the pinned action's
[permissions and event guidance](https://github.com/actions/labeler#permissions).
The workflow and trusted configuration change only after they reach the base
branch; a PR does not activate its own labeler changes.

## Path Labels

Keep these labels present in GitHub before introducing a matching rule:

| Label | Purpose |
| ----- | ------- |
| `ai-instructions` | Agent instructions, provider adapters, skills, and managed AI-tool configuration. |
| `ansible` | Ansible playbooks, inventory, roles, or Galaxy requirements. |
| `automation` | Repository automation, Taskfile, Renovate, or release tooling. |
| `browser-policies` | Browser, Thunderbird, and VS Code enterprise policy automation. |
| `ci` | GitHub Actions and CI configuration. |
| `dependencies` | Dependency manifests, lockfiles, or update automation. |
| `documentation` | Documentation and Markdown changes. |
| `dotfiles` | User-level dotfiles payload or install flow. |
| `github` | GitHub repository metadata, templates, or workflows. |
| `inventory` | Ansible inventory and host variable ownership. |
| `nvim` | Neovim configuration, fixtures, or generated keymap docs. |
| `security` | Security-sensitive settings, privacy dotfiles, SSHD, sysctl, or policy surfaces. |
| `shell` | Shell startup files or shell test fixtures. |
| `system` | Opt-in Arch Linux workstation system role. |
| `tests` | Test fixtures, smoke tests, or validation harnesses. |

## Triage And Release Labels

| Label | Owner and purpose |
| ----- | ----------------- |
| `bug` | Bug report issue form. |
| `enhancement` | Configuration-change issue form. |
| `maintenance` | Maintenance issue form. |
| `triage` | Issue forms; remove after initial classification when appropriate. |
| `autorelease: pending` | Release Please owns the pending release PR. |
| `autorelease: tagged` | Release Please has published the release. |

Release Please lifecycle labels are state, not general-purpose tags; do not
rename, remove, or add them to ordinary PRs as part of area-label cleanup.

## Catalog Maintenance

The required labels were confirmed present through the GitHub API on
2026-09-30. There is no label synchronization job or second machine-readable
catalog. When introducing a label, update this catalog and its actual consumer,
then create the remote label only within an authorized metadata change.

Use `dependencies` for dependency work. Historical labels such as `deps` and
`bashrc`, plus GitHub's other manual triage labels, may remain on older issues;
they are not produced by these rules. Do not rename or delete remote labels
merely because local classification changed.
