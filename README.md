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

`go-task` runs `playbook_install.yml` only. That playbook loads
`roles/dotfiles`, validates the dotfiles contract, creates required user
directories, links managed payload files, and removes a small set of explicit
legacy user config paths.

## Repository Layout

| Path | Purpose |
| ---- | ------- |
| `dotfiles/` | Canonical user-level payload linked into `$HOME`. |
| `inventory/host_vars/this_host/` | Local host data split by dotfiles, system, security, and browser policy ownership. |
| `playbook_install.yml` | Default local user-level install playbook. |
| `playbook_system.yml` | Opt-in privileged Arch Linux workstation playbook. |
| `playbook_browser_policies.yml` | Opt-in privileged browser and VS Code policy playbook. |
| `roles/dotfiles/` | User-level dotfiles validation and symlink role. |
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
| `go-task vint` | Run Vint with Neovim syntax enabled for Vimscript payloads. |
| `go-task verify` | Run the local aggregate validation path. |
| `go-task test:nvim` | Run the isolated Neovim smoke test. |
| `go-task test:nvim:profile` | Run the Neovim smoke test, then print startup and loaded-plugin counts. |
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
- `roles/dotfiles`
- explicit symlink mappings from `inventory/host_vars/this_host/dotfiles.yml`
- explicit cleanup entries from `dotfiles_cleanup_paths`

Add new managed payload files under `dotfiles/` and add matching mapping
entries in `inventory/host_vars/this_host/dotfiles.yml`. Mapping entries use
`name`, repository-relative `payload`, and absolute `dest`; the role computes
the source path and creates destination parent directories automatically. Do
not add secrets, browser profiles, caches, local databases, generated test
workspaces, SSH private keys, or GPG private keys.

## Neovim

The Neovim payload uses a structured `lazy.nvim` setup:

- `init.lua` loads core config first, then the plugin layer.
- `lua/config/lazy.lua` bootstraps `lazy.nvim` and honors the pinned
  `lazy.nvim` commit in `lazy-lock.json`.
- `lua/config/languages.lua` is the shared source for Tree-sitter languages
  and install requirements, LSP server binaries, Mason package lists,
  formatters, and linters.
- `lua/config/filetypes.lua` owns plugin-independent filetype detection so
  filetype-lazy plugins work for the first opened buffer.
- `lua/plugins/` contains all plugin specs; there is no separate kickstart
  plugin layer.
- `NVIM_USE_MASON=off` is the default. Use `auto` or `always` only when this
  host should let Mason install missing tools.
- Unused Node.js, Perl, and Ruby remote plugin providers are disabled by
  default; Python remains enabled for `python-pynvim`.

Neovim 0.11+ gets the modern LSP path via `vim.lsp.config()` and
`vim.lsp.enable()`. Neovim 0.10 keeps LSP through the legacy `nvim-lspconfig`
setup API. Older Neovim versions keep the core editor config and skip modern
plugins that cannot safely run there. Tree-sitter parser installs need the
`tree-sitter` CLI (`tree-sitter-cli` on Arch Linux), a C compiler, and `curl`;
`go-task test:nvim` skips that parser install step when those tools are missing
instead of producing noisy compile failures. Cold installs are validated by
`go-task test:nvim`, including a lockfile drift check after `Lazy restore`.
Startup-sensitive changes can be measured with `go-task test:nvim:profile`.

## Inventory Ownership

Host variables are split by ownership to keep reviews small and reduce
accidental conflicts:

| File | Owns |
| ---- | ---- |
| `inventory/host_vars/this_host/dotfiles.yml` | User-level mappings, extra directories, and cleanup paths. |
| `inventory/host_vars/this_host/system.yml` | Non-security system settings such as MOTD and journald. |
| `inventory/host_vars/this_host/security.yml` | SSHD, sysctl, and limits hardening settings. |
| `inventory/host_vars/this_host/browser_policies.yml` | Browser and VS Code policy overrides. |

Keep host variables role-prefixed: `dotfiles_*`, `system_*`, or
`browser_policies_*`. Upstream configuration keys inside settings maps keep
their native casing, for example SSHD, journald, sysctl, Chromium, Firefox,
and VS Code policy keys.

## System Layer

System-wide workstation configuration is opt-in:

```bash
go-task system:check
go-task system
```

This path runs `playbook_system.yml`, uses `roles/system`, and may require
sudo. It manages Arch Linux packages, system drop-ins, selected `/etc`
configuration, sysctl values, PAM limits, Docker daemon and overlay settings,
cron, reflector, and laptop-related settings.

The system role ships conservative default tuning for workstation use:

- sysctl defaults for unprivileged BPF, `fq`, BBR, `somaxconn`, and local port
  range.
- PAM limits through `/etc/security/limits.d/10-dotfiles.conf`.
- Docker overlay module options through `/etc/modprobe.d/99-dotfiles-overlay.conf`.

Host-specific additions and overrides belong in
`inventory/host_vars/this_host/security.yml`; keep role-owned defaults in
`roles/system/defaults/main.yml`.

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
go-task vint
```

Use the aggregate local check before finishing broad repository, role,
inventory, documentation, or automation changes:

```bash
go-task verify
```

Additional checks by area:

- User dotfiles or symlink mappings: `go-task`
- Full local validation: `go-task verify`
- Vimscript payloads: `go-task vint`
- Neovim config: `go-task test:nvim`
- Neovim startup-sensitive changes: `go-task test:nvim:profile`
- System role behavior: `go-task system:check` and `go-task test:system`
- Browser policy behavior: `go-task browser-policies:check`
- CI or repository-wide lint changes: `go-task superlinter`

`go-task superlinter` requires Docker.

## Repository Automation

GitHub issue forms and the PR template live under `.github/`. The labeler is
path-based and mirrors the current repository structure, including dotfiles,
inventory, roles, tests, automation, and AI instructions.

GitHub Copilot review guidance lives in `.github/copilot-instructions.md`,
with path-specific rules under `.github/instructions/`.

Renovate manages supported dependency updates for GitHub Actions, pre-commit,
Ansible Galaxy requirements, the Python toolchain, and the Super-Linter Docker
image referenced by `Taskfile.yml`.

Documentation and AI instructions are part of the repository contract. Update
`README.md`, the nearest `AGENTS.md`, `.github/copilot-instructions.md`, and
path-specific `.github/instructions/*.instructions.md` whenever commands,
roles, inventory ownership, validation paths, automation, or runtime behavior
change.

## Safety Notes

- Keep the default `go-task` workflow sudo-free.
- Keep privileged behavior behind explicit opt-in tasks.
- Prefer drop-ins and snippets over editing upstream main config files where
  supported.
- Keep generated and machine-local state out of git.
- Keep repository text, comments, and documentation in English.
