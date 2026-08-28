# Architecture

This repository is a personal Arch Linux dotfiles and workstation automation
baseline managed with Ansible, `uv`, and `go-task`.

It keeps user-owned dotfiles, opt-in system provisioning, opt-in browser,
Thunderbird, and VS Code policies, and repository validation in one place
without changing the default execution boundary.

This document is the canonical description of the repository architecture and
safety boundaries. `README.md` and `AGENTS.md` link here instead of restating
the layer model.

## Layer Model

| Layer | Entry points | Purpose |
| ----- | ------------ | ------- |
| User dotfiles | `go-task`, `playbook_install.yml`, `roles/dotfiles/` | Link managed files from `dotfiles/` into `$HOME` and remove explicit legacy user paths. |
| System workstation | `go-task system:check`, `go-task system`, `playbook_system.yml`, `roles/system/` | Check or apply the opt-in Arch Linux workstation layer. |
| Browser, Thunderbird, and VS Code policies | `go-task browser-policies:check`, `go-task browser-policies`, `playbook_browser_policies.yml`, `roles/browser_policies/` | Check or apply opt-in system policy files under `/etc`. |
| All opt-in apply | `go-task all` | Apply user dotfiles, system workstation, and browser policy layers in order. |
| Validation, reporting, and dependencies | `Taskfile.yml`, `.github/`, `.test/workstation_report.py`, Renovate, `uv.lock` | Keep local reports, validation, CI, linting, dependency updates, and generated docs reproducible. |

Host-specific values live under `inventory/host_vars/this_host/` and stay split
by ownership: dotfiles mappings, system settings, security-sensitive
workstation settings, and browser policy overrides.

## Environment Contract

| Environment | User dotfiles | System role | Policy role | Evidence |
| ----------- | ------------- | ----------- | ----------- | -------- |
| Arch bare metal or laptop | Supported | Supported; physical-only tasks are explicit and timesyncd is the time backend | Supported | Local check/apply paths and role validation |
| Arch virtual machine | Supported | Supported; hardware tasks are skipped and Chrony is the time backend | Supported | Backend contract assertions plus check/apply verification on a real guest |
| Arch container | Supported for integration tests | Container-safe subset only; systemd, Docker daemon, SSHD, sysctl, AUR, and hardware branches are skipped | Supported | `go-task test:system` first apply, assertions, and zero-change second apply |
| Ubuntu or macOS | User layer only | Unsupported | Unsupported | Default-playbook CI matrix |

The container test proves convergence only for branches that can safely run in
an unprivileged container. A real VM or host is required to exercise systemd,
Docker daemon restart, SSHD, sysctl loading, AUR package execution, and hardware
behavior. Those gaps are explicit; tests must not falsify facts merely to make
the branches appear covered.

On manageable systemd hosts, the system role selects exactly one time daemon:
Chrony on virtual machines and `systemd-timesyncd` on physical hosts. It
unmasks the selected service and masks other known NTP daemons. Containers and
CI select no backend. The native role contract proves selection logic; only a
real host can prove service activation and clock synchronization.

## AI Tool Contract

| Concern | Canonical surface | Adapters |
| ------- | ----------------- | -------- |
| Always-on repository rules | Root and nearest `AGENTS.md` | `CLAUDE.md`, `GEMINI.md`, condensed Copilot review deltas |
| Task-specific workflow | `.agents/skills/*/SKILL.md` | Native discovery in Codex and GitHub Copilot; other agents still follow the referenced ADR and Taskfile |
| Deterministic local guard | Managed Codex hook | Runs only for its declared tool event; it does not inject files or credentials into model context |
| External knowledge or actions | Explicit MCP/app profile | Disabled unless the workflow needs it; credentials and writable state stay local |
| Observable correctness | `go-task` targets and Ansible assertions | The same commands run locally, in containers, CI, and agent environments with the required tools |

Instructions define durable constraints; skills route repeatable work; hooks
enforce a small deterministic event policy; MCP servers connect external data.
Keeping those responsibilities separate avoids prompt duplication and makes
the repository usable from Codex local/cloud, GitHub Copilot, Claude Code, and
Gemini CLI without copying the engineering contract.

## Safety Model

- The default `go-task` path runs `playbook_install.yml` only and is sudo-free.
- Privileged workstation and policy layers require explicit commands.
- `go-task all` is an explicit privileged aggregate apply target, not the
  default workflow.
- System configuration prefers drop-ins and snippets where upstream supports
  them.
- AUR helper bootstrap lives in the opt-in system layer, uses tag `aur`, and is
  skipped in check mode, CI, and containers.
- Cleanup and removal paths should stay explicit, narrow, and reviewable.
- Check mode is available for privileged layers through `go-task system:check`
  and `go-task browser-policies:check`.
- Read-only reports are available through `go-task doctor`,
  `go-task dotfiles:plan`, `go-task system:report`, and
  `go-task browser-policies:report`.
- Privacy and policy configs manage documented settings only and must not
  include account state, credentials, profiles, or runtime histories.

## Former ans-workstation Layer

The former standalone `tenhishadow/ans-workstation` automation has been
consolidated into this repository as the opt-in system workstation layer.

The main locations are `roles/system/`, `playbook_system.yml`, and the
`system.yml` and `security.yml` host var files under
`inventory/host_vars/this_host/`. The default dotfiles install path remains
separate and must not apply system-wide configuration.
