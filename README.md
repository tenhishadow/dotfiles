# dotfiles

Personal Arch Linux dotfiles and workstation automation managed with Ansible
and `go-task`.

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)

This repository contains the user-level dotfiles workflow and the former
`ans-workstation` system automation layer. The default workflow remains
intentionally user-level and sudo-free: it links managed files from
`dotfiles/` into `$HOME`. System-wide workstation configuration and browser,
Thunderbird, and VS Code policies are available only through explicit opt-in
playbooks and `go-task` targets.

## Requirements

- Arch Linux
- `git`
- `go-task`
- `uv`
- `sudo` for opt-in system or policy tasks
- Docker for full validation, Super-Linter, and container-based smoke tests

Install the base tools:

```bash
sudo pacman -Sy --noconfirm --needed git go-task uv
```

## Quick Start

Clone the repository:

```bash
_INSTALL_DIR="$HOME/.dotfiles" \
  && git clone https://github.com/tenhishadow/dotfiles.git "$_INSTALL_DIR" \
  && cd "$_INSTALL_DIR"
```

Start with the user-level dry run:

```bash
go-task dotfiles:check
```

Apply the user-level dotfiles:

```bash
go-task
```

`go-task` runs `playbook_install.yml` only. That playbook loads
`roles/dotfiles`, validates the dotfiles contract, creates required user
directories, links managed payload files, and removes a small set of explicit
legacy user config paths.

## First-Run Safety

`go-task dotfiles:check` runs the default Ansible playbook in check mode with
diff output. The default playbook is user-level, uses `become: false`, and
loads `roles/dotfiles` only. It does not apply privileged system or browser
policy configuration.

Taskfile dependency bootstrap runs before Ansible and may install missing local
prerequisites such as `uv` or `git` through `pacman` and `sudo` on Arch Linux.
The dotfiles workflow can still replace managed destinations with symlinks and
remove explicit legacy user paths, so review
`inventory/host_vars/this_host/dotfiles.yml` before applying it on another
account or fork.

Do not run `go-task system`, `go-task browser-policies`, or `go-task all`
until you have reviewed managed `/etc` paths, Docker group behavior,
SSHD/sysctl values, the system package manifest, and browser/Thunderbird/VS
Code policy ownership.

Use read-only reports for a local view before applying changes:

```bash
go-task doctor
go-task dotfiles:plan
go-task system:report
go-task browser-policies:report
```

## Project Evolution

`tenhishadow/ans-workstation` previously contained the standalone Arch Linux
workstation automation. That layer has been consolidated into this repository.
The consolidation did not change the execution boundary:

- `go-task` / `playbook_install.yml` remains user-level and sudo-free.
- `go-task system` / `playbook_system.yml` applies the opt-in system layer.
- `go-task browser-policies` / `playbook_browser_policies.yml` applies the
  opt-in browser, Thunderbird, and VS Code policy layer.
- `go-task all` applies those three layers in order and is an explicit
  privileged opt-in aggregate.

The default dotfiles install path must not apply privileged configuration.

## Execution Layers

| Layer | Command | Privileged | Purpose |
| ---- | ------- | ---------- | ------- |
| User dotfiles | `go-task` | No | Link managed dotfiles into `$HOME`. |
| System workstation | `go-task system:check` / `go-task system` | Yes | Check or apply the opt-in Arch Linux workstation layer. |
| Browser policies | `go-task browser-policies:check` / `go-task browser-policies` | Yes | Check or apply opt-in browser, Thunderbird, and VS Code policies. |
| All opt-in apply | `go-task all` | Yes | Apply user dotfiles, system workstation, and browser policy layers in order. |
| Validation | `go-task verify` | No direct system apply | Run repository validation, linting, documentation checks, and smoke tests. |

Check targets run after Taskfile dependency bootstrap. `go-task system:check`
then runs `playbook_system.yml` in Ansible check mode with diff output.

## Repository Layout

| Path | Purpose |
| ---- | ------- |
| `dotfiles/` | Canonical user-level payload linked into `$HOME`. |
| `inventory/host_vars/this_host/` | Local host data split by dotfiles, system, security, and browser policy ownership. |
| `playbook_install.yml` | Default local user-level install playbook. |
| `playbook_system.yml` | Opt-in privileged Arch Linux workstation playbook. |
| `playbook_browser_policies.yml` | Opt-in privileged browser, Thunderbird, and VS Code policy playbook. |
| `roles/dotfiles/` | User-level dotfiles validation and symlink role. |
| `roles/system/` | Arch Linux workstation system provisioning role. |
| `roles/browser_policies/` | Enterprise browser, Thunderbird, and VS Code policy role. |
| `docs/` | Architecture, adoption, security, migration, and generated operator manuals. |
| `.github/` | GitHub Actions, issue forms, PR template, labeler, and release automation. |
| `.test/` | Isolated smoke-test fixtures and container test entry points. |

## Documentation

| Document | Purpose |
| -------- | ------- |
| [`docs/architecture.md`](docs/architecture.md) | Repository layer model and safety boundaries. |
| [`docs/adoption.md`](docs/adoption.md) | Practical first-use and forking notes. |
| [`docs/security-notes.md`](docs/security-notes.md) | Security caveats for this personal workstation baseline. |
| [`docs/privacy-policy-surfaces.md`](docs/privacy-policy-surfaces.md) | Managed privacy, policy, and user-dotfile surfaces. |
| [`docs/migration-from-ans-workstation.md`](docs/migration-from-ans-workstation.md) | Location map for the former `ans-workstation` layer. |
| [`docs/github-labels.md`](docs/github-labels.md) | GitHub labeler pipeline and repository label expectations. |
| [`roles/system/README.md`](roles/system/README.md) | System role managed paths, validation, and rollback notes. |
| [`roles/browser_policies/README.md`](roles/browser_policies/README.md) | Browser, Thunderbird, and VS Code policy targets, variables, and rollback notes. |

## Common Tasks

This table is the single source of truth for the `go-task` command catalog.
Other documentation references these commands by name instead of repeating the
table.

| Command | Purpose |
| ------- | ------- |
| `go-task` | Apply user-level dotfiles only. |
| `go-task all` | Apply user dotfiles, then the opt-in system and browser policy layers. |
| `go-task dotfiles:check` | Dry-run the user-level dotfiles playbook with diff output. |
| `go-task dotfiles:plan` | Print existing user dotfile destinations and cleanup paths. |
| `go-task doctor` | Print read-only local tool, managed user-tool, Docker, user, and systemd availability. |
| `go-task lint` | Run `ansible-lint` for playbooks, inventory, and roles. |
| `go-task yamllint` | Run YAML linting through the pinned `uv` environment. |
| `go-task vint` | Run Vint with Neovim syntax enabled for Vimscript payloads. |
| `go-task docs:nvim-keymaps` | Regenerate the Neovim keymap manual. |
| `go-task docs:nvim-keymaps:check` | Check that the generated Neovim keymap manual is current. |
| `go-task verify` | Run the full local aggregate validation path, including Docker-backed checks. |
| `go-task superlinter` | Run the GitHub Super-Linter container locally. |
| `go-task test:nvim` | Run the isolated Neovim smoke test. |
| `go-task test:nvim:mason-tools` | Validate configured Mason package names against the Mason registry. |
| `go-task test:nvim:profile` | Run the Neovim smoke test, then print startup and loaded-plugin counts. |
| `go-task system:list` | List tasks in the opt-in system playbook. |
| `go-task system:report` | Print managed system paths and local Docker/SSHD status. |
| `go-task system:check` | Bootstrap dependencies, then dry-run the opt-in system playbook. |
| `go-task system` | Apply the opt-in system playbook. |
| `go-task test:system` | Check system package targets, smoke, and idempotency in an Arch Linux container. |
| `go-task browser-policies:report` | Print managed browser, Thunderbird, and VS Code policy app versions and expected policy paths. |
| `go-task browser-policies:check` | Dry-run system browser, Thunderbird, and VS Code policy management. |
| `go-task browser-policies` | Apply system browser, Thunderbird, and VS Code policy management. |
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

The managed user payload includes privacy-focused configs for Gemini CLI, K9s,
Git Delta, Terraform CLI, bat, ripgrep, btop, direnv, npm, Yarn, and pip. These
configs are normal dotfiles and do not include account state, kubeconfigs,
tokens, private registries, AI conversation history, or runtime profiles. See
[`docs/privacy-policy-surfaces.md`](docs/privacy-policy-surfaces.md) for the
managed surface list and intentionally unmanaged files.

Generated `xdg-user-dirs` state such as `~/.config/user-dirs.dirs` is not
managed. `xdg-user-dirs-update` rewrites that path as a regular local file, so
linking it from the repository would make the default dotfiles run non-idempotent.

`go-task doctor` reports availability and versions for these managed user tools
without reading credentials, kubeconfigs, cloud auth, browser profiles, or mail
profiles.

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
- `lua/config/keymaps_spec.lua` is the source of truth for user-facing
  keymaps and generated keymap documentation.
- `lua/plugins/` contains all plugin specs; there is no separate kickstart
  plugin layer.
- Automatic linting is save-triggered and limited to lightweight file-local
  linters. Heavier project-wide linters are available manually through
  `:DotfilesLintManual` or explicit validation commands for Kubernetes, Helm,
  Kustomize, Terraform/OpenTofu, Trivy, Gitleaks, and Semgrep.
- Formatters are configured for explicit manual use only. Saving a file must
  not auto-format content or strip whitespace.
- `NVIM_USE_MASON=off` is the default. `auto` makes already-installed Mason
  tools available without startup installs; `always` allows Mason to install
  configured missing tools on startup.
- Unused Node.js, Perl, and Ruby remote plugin providers are disabled by
  default; Python remains enabled for `python-pynvim`.

Neovim 0.11.3+ gets the modern LSP path via `vim.lsp.config()` and
`vim.lsp.enable()`. Older Neovim versions keep the core editor config and skip
the LSP plugin layer because current upstream `nvim-lspconfig` requires
Neovim 0.11.3+. Tree-sitter parser installs need the
`tree-sitter` CLI (`tree-sitter-cli` on Arch Linux), a C compiler, and `curl`;
`go-task test:nvim` skips that parser install step when those tools are missing
instead of producing noisy compile failures. Cold installs are validated by
`go-task test:nvim`, including a lockfile drift check after `Lazy restore` and
Mason registry package-name validation for configured Mason tools.
Startup-sensitive changes can be measured with `go-task test:nvim:profile`.
User-facing keymaps are documented in `docs/nvim-keymaps.md`; regenerate it
with `go-task docs:nvim-keymaps` after keymap changes.

## Inventory Ownership

Host variables are split by ownership to keep reviews small and reduce
accidental conflicts:

| File | Owns |
| ---- | ---- |
| `inventory/host_vars/this_host/dotfiles.yml` | User-level mappings, extra directories, and cleanup paths. |
| `inventory/host_vars/this_host/system.yml` | Non-security system settings such as MOTD and journald. |
| `inventory/host_vars/this_host/security.yml` | SSHD, sysctl, and limits security-sensitive workstation settings. |
| `inventory/host_vars/this_host/browser_policies.yml` | Browser, Thunderbird, and VS Code policy overrides. |

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
cron, reflector, optional AUR `yay` bootstrap, and laptop-related settings.

The system role ships role-owned default tuning for workstation use:

- sysctl defaults for unprivileged BPF, `fq`, BBR, `somaxconn`, and local port
  range.
- PAM limits through `/etc/security/limits.d/10-dotfiles.conf`.
- AUR helper bootstrap through tasks tagged `aur`, skipped in check mode, CI,
  and containers.
- Docker overlay module options through `/etc/modprobe.d/99-dotfiles-overlay.conf`.

Host-specific additions and overrides belong in
`inventory/host_vars/this_host/security.yml`; keep role-owned defaults in
`roles/system/defaults/main.yml`.

See `roles/system/README.md` for managed paths, validation, and rollback
notes.

## Browser Policies

Browser, Thunderbird, and VS Code enterprise policies are opt-in:

```bash
go-task browser-policies:check
go-task browser-policies
```

This path writes root-owned policy files under `/etc` and intentionally does
not manage runtime browser, Thunderbird, or VS Code profile state. See
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

`go-task verify` includes the system role container test and GitHub
Super-Linter container, so it requires a running Docker daemon. Use the
narrower area-specific checks above only when Docker is unavailable and state
that limitation in review notes.

Additional checks by area:

- User dotfiles or symlink mappings: `go-task dotfiles:check`, then `go-task`
- Full local validation, including Docker-backed checks: `go-task verify`
- Vimscript payloads: `go-task vint`
- Neovim keymap docs: `go-task docs:nvim-keymaps:check`
- Neovim config: `go-task test:nvim`
- Neovim Mason tool inventory: `go-task test:nvim:mason-tools`
- Neovim startup-sensitive changes: `go-task test:nvim:profile`
- System role packages and behavior: `go-task system:check` and
  `go-task test:system`
- Browser policy behavior: `go-task browser-policies:check`
- CI or repository-wide lint changes: `go-task superlinter`

`go-task verify` and `go-task superlinter` require Docker.

## Repository Automation

GitHub issue forms and the PR template live under `.github/`. The labeler is
path-based and mirrors the current repository structure, including dotfiles,
inventory, roles, tests, automation, and AI instructions. Label expectations
are documented in [`docs/github-labels.md`](docs/github-labels.md).

The `ansible` workflow also runs a `task-all` job in an Arch Linux container.
It executes `go-task all -- --skip-tags pkg,aur` to cover aggregate ordering across
the user dotfiles, system, and browser policy layers without installing the
full workstation package manifest or AUR helper on hosted runners.

GitHub Copilot review guidance lives in `.github/copilot-instructions.md`,
with path-specific rules under `.github/instructions/`.

Renovate manages supported dependency updates for GitHub Actions, pre-commit,
Ansible Galaxy requirements, the Python toolchain, and the Super-Linter Docker
image referenced by `Taskfile.yml`. Renovate intentionally ignores `.test/`
fixtures because they are detector and smoke-test inputs, not repository
dependency surfaces.

Use `go-task deps-upgrade` for local, reviewable dependency refreshes. It
updates `uv.lock`, refreshes the installed Ansible Galaxy collections allowed by
`requirements.yml`, runs `pre-commit autoupdate`, updates Neovim
`lazy-lock.json`, and validates Renovate config. GitHub Actions are updated by
Renovate PRs; use `go-task deps-report:github-actions` when you want a local
Renovate extraction/dry-run report for workflow dependencies.

Documentation and AI instructions are part of the repository contract. The
[Common Tasks](#common-tasks) table is the single source of truth for the
`go-task` command catalog: update it when commands change, and reference
commands by name elsewhere instead of repeating the table. Update the nearest
`AGENTS.md`, `.github/copilot-instructions.md`, and path-specific
`.github/instructions/*.instructions.md` whenever roles, inventory ownership,
validation paths, automation, or runtime behavior change.

## Safety Notes

- Keep the default `go-task` workflow sudo-free.
- Keep privileged behavior behind explicit opt-in tasks.
- Prefer drop-ins and snippets over editing upstream main config files where
  supported.
- Keep generated and machine-local state out of git.
- Keep repository text, comments, and documentation in English.
