# dotfiles

Personal dotfiles and Arch Linux workstation automation managed with Ansible,
`uv`, and `go-task`.

[![ansible](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml/badge.svg)](https://github.com/tenhishadow/dotfiles/actions/workflows/ansible.yml)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/tenhishadow/dotfiles)

The default workflow is user-level and sudo-free. Privileged workstation and
browser policy changes remain explicit opt-ins. The former
`tenhishadow/ans-workstation` automation now lives here under that boundary.

## Requirements

- `git`, `go-task`, and `uv`
- Arch Linux and `sudo` for the opt-in system and policy layers
- Docker for full local validation
- Node.js and npm for repository validation and the managed Codex/MCP runtimes

On Arch Linux:

```bash
sudo pacman -Syu --needed git go-task uv
```

The default task checks these prerequisites but never installs them or invokes
`sudo`. Environment support and test coverage are defined in
[`docs/architecture.md`](docs/architecture.md).

## Quick Start

```bash
git clone https://github.com/tenhishadow/dotfiles.git "$HOME/.dotfiles"
cd "$HOME/.dotfiles"
go-task dotfiles:check
go-task
```

`go-task` runs `playbook_install.yml` only. It validates mappings, links
payloads from `dotfiles/` into `$HOME`, and removes only the explicit legacy
paths declared in `inventory/host_vars/this_host/dotfiles.yml`.

Before using this repository on another account or fork, review that inventory
file. Before any privileged apply, inspect the read-only reports:

```bash
go-task doctor
go-task dotfiles:plan
go-task system:report
go-task browser-policies:report
```

## Execution Layers

| Layer | Check or report | Apply | Privileged |
| ----- | --------------- | ----- | ---------- |
| User dotfiles | `go-task dotfiles:check` | `go-task` | No |
| Arch workstation | `go-task system:check` | `go-task system` | Yes |
| Browser, Thunderbird, and VS Code policies | `go-task browser-policies:check` | `go-task browser-policies` | Yes |
| All layers | Individual checks above | `go-task all` | Yes |

`go-task all` is an explicit aggregate, not the default. The canonical layer
and safety model is in [`docs/architecture.md`](docs/architecture.md).

## Common Tasks

This table is the canonical operator command reference. Internal helper tasks
remain discoverable with `go-task --list-all`.

| Command | Purpose |
| ------- | ------- |
| `go-task` | Apply user-level dotfiles only. |
| `go-task all` | Apply user dotfiles, system configuration, and policies in order. |
| `go-task dotfiles:check` | Dry-run the user-level playbook with diff output. |
| `go-task dotfiles:plan` | Report current mapping destinations and cleanup paths. |
| `go-task doctor` | Report local tool and runtime availability without reading credentials. |
| `go-task system:check` | Dry-run the opt-in Arch workstation playbook. |
| `go-task system` | Apply the opt-in Arch workstation playbook. |
| `go-task system:list` | List system playbook tasks. |
| `go-task system:report` | Report managed system paths and relevant local services. |
| `go-task browser-policies:check` | Dry-run policy management. |
| `go-task browser-policies` | Apply system policy files. |
| `go-task browser-policies:report` | Report expected policy paths and installed applications. |
| `go-task test:system` | Validate package targets and convergence of all layers in a disposable Arch container. |
| `go-task verify:fast` | Run static repository checks without Docker or managed-host writes. |
| `go-task verify` | Run the full local validation aggregate, including Docker-backed checks. |
| `go-task lint` | Run `ansible-lint`. |
| `go-task lint:markdown` | Lint every tracked Markdown file with the shared repository rules. |
| `go-task lint:python` | Lint and format-check repository Python. |
| `go-task yamllint` | Lint YAML through the locked Python environment. |
| `go-task vint` | Lint Vimscript with Neovim syntax enabled. |
| `go-task test:nvim` | Run the isolated Neovim smoke test. |
| `go-task test:nvim:profile` | Run the Neovim smoke test and report startup metrics. |
| `go-task docs:nvim-keymaps` | Regenerate the Neovim keymap manual. |
| `go-task docs:nvim-keymaps:check` | Verify that the keymap manual is current. |
| `go-task superlinter` | Run Super-Linter locally in Docker. |
| `go-task codex:install` | Install lockfile-resolved Codex, Context7, and Playwright packages. |
| `go-task codex:mcp:install` | Install only the lockfile-resolved MCP packages. |
| `go-task pacdiff` | List pending pacman `.pacnew` and `.pacsave` files. |

## Repository Layout

| Path | Purpose |
| ---- | ------- |
| `dotfiles/` | Canonical user payload linked into `$HOME`. |
| `inventory/host_vars/this_host/` | Dotfiles mappings, system values, security values, and policy overrides. |
| `roles/dotfiles/` | Default user-level role. |
| `roles/system/` | Opt-in Arch workstation role. |
| `roles/browser_policies/` | Opt-in policy role. |
| `.test/` | Static checks, isolated fixtures, and the Arch convergence harness. |
| `.agents/skills/` | Repository workflows shared by Codex and GitHub Copilot. |
| `AGENTS.md` | Canonical repository instructions for AI agents. |
| `CLAUDE.md` / `GEMINI.md` | Native provider adapters importing `AGENTS.md`. |
| `docs/` | Architecture, ADRs, security, privacy, adoption, and migration notes. |

## AI Tooling

Always-on repository rules live once in `AGENTS.md`; nearest nested
`AGENTS.md` files add path-local deltas. Claude Code and Gemini CLI import the
same contract through their native root files. Task-specific workflows belong
in `.agents/skills/`: `validate-dotfiles-change` routes a diff to the smallest
useful test, while `write-markdown` applies the shared documentation contract.

The managed user payload places Ponytail 4.9.0 in `~/.agents/skills/`, the
cross-agent user skill location. Codex profiles, hooks, launchers, manifests,
and lockfiles are linked from `dotfiles/`; writable authentication, trust,
history, databases, credentials, and `~/.codex/config.toml` remain local.
`go-task codex:install` uses `npm ci`; agent startup never downloads packages.

Context7 and the official OpenAI documentation server are sufficient for this
repository's public documentation work. Playwright, Grafana, and GitHub writes
remain disabled unless a dedicated profile enables them. See
[`docs/privacy-policy-surfaces.md`](docs/privacy-policy-surfaces.md) and the
historical [Codex decision chain](docs/decision-chain-2026-08-13-codex-tooling.md).

## Validation

Use the narrowest command that observes the changed behavior. Broad changes
finish with:

```bash
go-task verify
```

`go-task verify` does not apply configuration to the local workstation. It
runs static checks, isolated Neovim checks, convergence of all three Ansible
layers in a disposable Arch container, and Super-Linter. The convergence test
requires a successful first apply, post-install assertions, and a second apply
with zero changes. Check mode remains a preview, not an idempotency proof.

The decision and framework escalation criteria are recorded in
[`docs/adr/0001-validation-strategy.md`](docs/adr/0001-validation-strategy.md).

For repeated container runs, copy `.test/system/local.env.example` to
`.test/system/local.env`, then uncomment and set either optional mirror. The
file is loaded automatically, ignored by Git, and masked from the Super-Linter
container. Without it, public upstream sources remain the default.

```bash
cp .test/system/local.env.example .test/system/local.env
chmod 600 .test/system/local.env
go-task test:system
```

The pacman URL must be an HTTPS `Server` template containing literal `$repo`
and `$arch` placeholders. The Python URL must be an HTTPS PEP 503 index. The
harness exports exact requirements and hashes from `uv.lock`, installs them
through that index, and disables later project syncs so a private URL cannot
enter the lock file. Configured mirrors fail closed instead of falling back to
public sources. Select another env file for a one-off run with
`DOTFILES_TEST_ENV_FILE=/absolute/path go-task test:system`.

## Operator Documentation

- [`docs/architecture.md`](docs/architecture.md): layers, environments, and safety boundaries
- [`docs/adoption.md`](docs/adoption.md): first-use and forking guidance
- [`docs/security-notes.md`](docs/security-notes.md): personal-baseline security caveats
- [`docs/privacy-policy-surfaces.md`](docs/privacy-policy-surfaces.md): managed privacy and AI-client surfaces
- [`docs/migration-from-ans-workstation.md`](docs/migration-from-ans-workstation.md): former repository location map
- [`roles/dotfiles/README.md`](roles/dotfiles/README.md): user role contract
- [`roles/system/README.md`](roles/system/README.md): system variables, paths, validation, and rollback
- [`roles/browser_policies/README.md`](roles/browser_policies/README.md): policy targets, validation, and rollback

GitHub Actions runs the user-level path on Linux and macOS and runs the full
Arch convergence harness on pull requests, pushes, and a weekly fresh-image
schedule. Renovate owns supported dependency updates. Repository instructions,
skills, labels, and documentation are validated as code; no MCP server or AI
account state is committed.
