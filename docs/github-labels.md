# GitHub Labels

GitHub labels are repository metadata. Pull request path labels are declared in
`.github/labeler.yml` and applied by `.github/workflows/labeler.yml`.

## Pipeline

- The labeler workflow runs on pull requests.
- `.github/labeler.yml` is the source for path-based label rules.
- `sync-labels: false` preserves manually added labels and issue-form labels.
- `changed-files-labels-limit` must stay above the number of path labels a
  broad maintenance pull request can match. If that limit is exceeded,
  `actions/labeler` skips all changed-file labels.

## Path Labels

Keep these GitHub labels present when editing `.github/labeler.yml`:

| Label | Purpose |
| ----- | ------- |
| `ai-instructions` | AI agent and Copilot instruction changes. |
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

## Template Labels

Issue forms also use static labels such as `bug`, `enhancement`,
`maintenance`, and `triage`. Keep those labels present in GitHub when changing
issue templates.

Release Please uses `autorelease: pending` and `autorelease: tagged`.
