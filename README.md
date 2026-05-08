# dotfiles

Personal Arch Linux dotfiles and workstation automation managed with Ansible
and `go-task`.

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)

The default workflow is intentionally user-level only: it links files from
`dotfiles/` into `$HOME` and does not require sudo. System-wide configuration
is available through explicit opt-in tasks.

## Requirements

- Arch Linux
- `git`
- `go-task`
- `uv`
- `sudo` for opt-in system or policy tasks
- Docker for container-based smoke tests

Install the base tools:

```bash
sudo pacman -Sy --noconfirm --needed git go-task uv
```

## Quick Start

Clone and apply the user-level dotfiles:

```bash
_INSTALL_DIR="$HOME/.dotfiles" \
  && git clone https://github.com/tenhishadow/dotfiles.git "$_INSTALL_DIR" \
  && cd "$_INSTALL_DIR" \
  && go-task
```

`go-task` runs `playbook_install.yml` only. It creates required user
directories, links managed payload files, and removes a small set of explicit
legacy user config paths.

## Repository Layout

| Path | Purpose |
| ---- | ------- |
| `dotfiles/` | Canonical user-level payload linked into `$HOME`. |
| `inventory/host_vars/this_host.yml` | Local source of truth for mappings, cleanup, browser policy overrides, and system role values. |
| `playbook_install.yml` | Default local user-level install playbook. |
| `playbook_system.yml` | Opt-in privileged Arch Linux workstation playbook. |
| `playbook_browser_policies.yml` | Opt-in privileged browser and VS Code policy playbook. |
| `roles/system/` | Arch Linux workstation system provisioning role. |
| `roles/browser_policies/` | Enterprise browser and VS Code policy role. |
| `.github/` | GitHub Actions, issue forms, PR template, labeler, and release automation. |
| `.test/` | Isolated smoke-test fixtures and container test entry points. |

## Common Tasks

| Command | Purpose |
| ------- | ------- |
| `go-task` | Apply user-level dotfiles only. |
| `go-task lint` | Run `ansible-lint` for playbooks, inventory, and roles. |
| `go-task yamllint` | Run YAML linting through the pinned `uv` environment. |
| `go-task test:nvim` | Run the isolated Neovim smoke test. |
| `go-task system:list` | List tasks in the opt-in system playbook. |
| `go-task system:check` | Dry-run the opt-in system playbook. |
| `go-task system` | Apply the opt-in system playbook. |
| `go-task test:system` | Run the system role smoke and idempotency test in an Arch Linux container. |
| `go-task browser-policies:check` | Dry-run system browser and VS Code policy management. |
| `go-task browser-policies` | Apply system browser and VS Code policy management. |
| `go-task pacdiff` | List pending pacman `.pacnew` and `.pacsave` files. |

## User Dotfiles

User dotfiles are managed by `playbook_install.yml` with:

- `connection: local`
- `become: false`
- explicit symlink mappings from `inventory/host_vars/this_host.yml`
- explicit cleanup entries from `dotfiles_cleanup`

Add new managed payload files under `dotfiles/` and add matching mapping
entries in `inventory/host_vars/this_host.yml`. Do not add secrets, browser
profiles, caches, local databases, generated test workspaces, SSH private
keys, or GPG private keys.

## System Layer

System-wide workstation configuration is opt-in:

```bash
go-task system:check
go-task system
```

This path runs `playbook_system.yml`, uses `roles/system`, and may require
sudo. It manages Arch Linux packages, system drop-ins, selected `/etc`
configuration, Docker daemon settings, cron, reflector, and laptop-related
settings.

See `roles/system/README.md` for managed paths, validation, and rollback
notes.

## Browser Policies

Browser and VS Code enterprise policies are opt-in:

```bash
go-task browser-policies:check
go-task browser-policies
```

This path writes root-owned policy files under `/etc` and intentionally does
not manage runtime browser or VS Code profile state. See
`roles/browser_policies/README.md` for variables, validation, and rollback
notes.

## Validation

Use the narrowest validation that covers the change:

```bash
git diff --check
go-task lint
go-task yamllint
```

Additional checks by area:

- User dotfiles or symlink mappings: `go-task`
- Neovim config: `go-task test:nvim`
- System role behavior: `go-task system:check` and `go-task test:system`
- Browser policy behavior: `go-task browser-policies:check`
- CI or repository-wide lint changes: `go-task superlinter`

`go-task superlinter` requires Docker.

## Repository Automation

GitHub issue forms and the PR template live under `.github/`. The labeler is
path-based and mirrors the current repository structure, including dotfiles,
inventory, roles, tests, automation, and AI instructions.

Renovate manages supported dependency updates for GitHub Actions, pre-commit,
Ansible Galaxy requirements, the Python toolchain, and the Super-Linter Docker
image referenced by `Taskfile.yml`.

## Safety Notes

- Keep the default `go-task` workflow sudo-free.
- Keep privileged behavior behind explicit opt-in tasks.
- Prefer drop-ins over editing upstream main config files where supported.
- Keep generated and machine-local state out of git.
- Keep repository text, comments, and documentation in English.
