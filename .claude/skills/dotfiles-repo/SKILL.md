---
name: dotfiles-repo
description: Orientation for this Arch Linux dotfiles repo (Ansible, go-task, uv, Neovim). Use when working in this repository to find the authoritative rules, the command catalog, and which validation to run. It links to the canonical docs instead of repeating them.
---

# dotfiles-repo

This is a thin pointer. The authoritative sources already live in the repo;
read them rather than relying on a copy here.

## Rules and conventions

- Read the nearest `AGENTS.md` before editing (root `AGENTS.md`, plus the
  nested ones under `.github/`, `.test/`, `dotfiles/`, `inventory/`, and
  `roles/`). They define the hard rules, naming, variable style, review rules,
  and the documentation-sync contract.
- Core contract: the default `go-task` stays user-level and sudo-free
  (`playbook_install.yml`, `roles/dotfiles` only); system and browser-policy
  layers are explicit privileged opt-ins.

## Commands

- The README `Common Tasks` table is the single source of truth for the
  `go-task` command catalog. Use it by name; do not re-list it elsewhere.

## Validation

- Pick the matching check from the AGENTS.md `Validation Matrix` (for example
  `go-task lint` for Ansible/Taskfile changes, `go-task dotfiles:check` for the
  dotfiles flow, `go-task system:check` and `go-task test:system` for the system
  role, `go-task browser-policies:check` for policies).
- Run `go-task verify` for a full local pass when several areas change together
  (needs a running Docker daemon).
