# Repository

Arch Linux dotfiles and workstation automation repository managed with
Ansible, `uv`, and `go-task`.

## Architecture

- `dotfiles/` contains the canonical user-level payload linked into `$HOME`.
- `playbook_install.yml` is the default user-level install playbook.
- `playbook_system.yml` is the explicit privileged workstation playbook.
- `playbook_browser_policies.yml` is the explicit privileged browser policy
  playbook.
- `inventory/host_vars/this_host.yml` is the local source of truth for
  symlink mappings, cleanup, browser policy overrides, and system role values.
- `roles/system/` contains opt-in Arch Linux workstation provisioning.
- `roles/browser_policies/` contains opt-in browser and VS Code policy
  management.

## Instruction Scope

- The nearest `AGENTS.md` applies.
- Nested `AGENTS.md` files add local rules and should not duplicate this file
  wholesale.
- Check local instructions before editing:
  - `.github/AGENTS.md`
  - `.test/AGENTS.md`
  - `dotfiles/AGENTS.md`
  - `dotfiles/.config/nvim/AGENTS.md`
  - `inventory/AGENTS.md`
  - `roles/AGENTS.md`
  - `roles/system/AGENTS.md`
  - `roles/system/vars/AGENTS.md`

## Hard Rules

- Preserve the default user-level dotfiles workflow.
- Do not make default `go-task` require sudo.
- Do not add `become: true` to `playbook_install.yml`.
- Do not add `roles/system` or `roles/browser_policies` to
  `playbook_install.yml`.
- Keep privileged and system-wide behavior behind explicit opt-in
  playbooks/tasks.
- Prefer service drop-ins over editing upstream main config files where
  supported.
- Keep changes deterministic, narrow, reviewable, and idempotent.
- Keep repository text, comments, task names, documentation, and AI
  instructions in English.
- Do not commit secrets, tokens, cookies, browser profiles, session state,
  local databases, caches, private keys, generated test workspaces, or copied
  runtime configs.

## Engineering Rules

- Prefer boring, upstream-compatible Ansible over custom shell.
- Use FQCN modules such as `ansible.builtin.file`.
- Use explicit ownership and mode for managed files, especially under `/etc`.
- Keep variables in inventory, role defaults, or role vars instead of
  duplicating literals.
- Keep package lists and policy target lists declarative.
- Use handlers for service restarts when template or config changes require
  them.
- Preserve CI and container guards for privileged system behavior.
- Do not broaden cleanup/removal patterns without an explicit requirement.

## Commit Rules

- Use Conventional Commits when a commit is requested.
- Keep commits scoped to the requested change.
- Do not push unless explicitly requested.
- Do not include unrelated dirty worktree changes.

## Validation Matrix

- Always run `git diff --check` before finishing non-trivial changes.
- Run `go-task` for user dotfiles, symlink mappings, cleanup, or default
  install flow changes.
- Run `go-task lint` for Ansible, inventory, role, Taskfile, or playbook
  changes.
- Run `uv run yamllint .` or `go-task yamllint` for YAML-heavy changes.
- Run `go-task test:nvim` for Neovim config changes.
- Run `go-task system:check` for system role changes.
- Run `go-task test:system` for system role task, template, or handler
  behavior changes when Docker is available.
- Run `go-task browser-policies:check` for browser policy role or policy
  inventory changes.
- Run `go-task superlinter` for CI or repository-wide lint changes when Docker
  is available.

## Done Criteria

- Applicable local `AGENTS.md` rules were followed.
- Runtime behavior changed only when required by the task.
- The default user-level dotfiles flow remains intact and sudo-free.
- Privileged behavior remains explicit and opt-in.
- Relevant validation commands were run or blockers were stated.
- No secrets or machine-local runtime state were added.
