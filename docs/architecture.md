# Architecture

This repository is a personal Arch Linux dotfiles and workstation automation
baseline managed with Ansible, `uv`, and `go-task`.

It keeps user-owned dotfiles, opt-in system provisioning, opt-in browser and VS
Code policies, and repository validation in one place without changing the
default execution boundary.

## Layer Model

| Layer | Entry points | Purpose |
| ----- | ------------ | ------- |
| User dotfiles | `go-task`, `playbook_install.yml`, `roles/dotfiles/` | Link managed files from `dotfiles/` into `$HOME` and remove explicit legacy user paths. |
| System workstation | `go-task system:check`, `go-task system`, `playbook_system.yml`, `roles/system/` | Check or apply the opt-in Arch Linux workstation layer. |
| Browser and VS Code policies | `go-task browser-policies:check`, `go-task browser-policies`, `playbook_browser_policies.yml`, `roles/browser_policies/` | Check or apply opt-in system policy files under `/etc`. |
| Validation and dependencies | `Taskfile.yml`, `.github/`, Renovate, `uv.lock` | Keep local validation, CI, linting, dependency updates, and generated docs reproducible. |

Host-specific values live under `inventory/host_vars/this_host/` and stay split
by ownership: dotfiles mappings, system settings, security-sensitive
workstation settings, and browser policy overrides.

## Safety Model

- The default `go-task` path runs `playbook_install.yml` only and is sudo-free.
- Privileged workstation and policy layers require explicit commands.
- System configuration prefers drop-ins and snippets where upstream supports
  them.
- Cleanup and removal paths should stay explicit, narrow, and reviewable.
- Check mode is available for privileged layers through `go-task system:check`
  and `go-task browser-policies:check`.

## Former ans-workstation Layer

The former standalone `tenhishadow/ans-workstation` automation has been
consolidated into this repository as the opt-in system workstation layer.

The main locations are `roles/system/`, `playbook_system.yml`, and the
`system.yml` and `security.yml` host var files under
`inventory/host_vars/this_host/`. The default dotfiles install path remains
separate and must not apply system-wide configuration.
