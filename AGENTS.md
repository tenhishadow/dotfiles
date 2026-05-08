# Repository

Arch Linux dotfiles and workstation automation repository managed with
Ansible, `uv`, and `go-task`.

## Architecture

- `dotfiles/` contains the canonical user-level payload linked into `$HOME`.
- `playbook_install.yml` is the default user-level install playbook.
- `playbook_system.yml` is the explicit privileged workstation playbook.
- `playbook_browser_policies.yml` is the explicit privileged browser policy
  playbook.
- `inventory/host_vars/this_host/` is the local source of truth for dotfiles
  mappings, cleanup, browser policy overrides, and system role values.
- `roles/dotfiles/` contains the default user-level dotfiles workflow.
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
  - `roles/dotfiles/AGENTS.md`
  - `roles/system/AGENTS.md`
  - `roles/system/vars/AGENTS.md`

## Hard Rules

- Preserve the default user-level dotfiles workflow.
- Do not make default `go-task` require sudo.
- Do not add `become: true` to `playbook_install.yml`.
- `playbook_install.yml` may include `roles/dotfiles` only. Do not add
  `roles/system` or `roles/browser_policies` to `playbook_install.yml`.
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

## Ansible Naming Style

- Use one format for all Ansible play, task, and handler names:
  `<Domain> | <Verb> <object>`.
- Keep domains short and stable, for example `Dotfiles`, `System`,
  `Browser Policies`, `SSHD`, `NTP`, `Docker`, and `User systemd`.
- Preserve upstream product casing such as `systemd`, `SSHD`, `VS Code`, and
  `Neovim`.
- Use concise imperative verbs such as `Apply`, `Add`, `Build`, `Check`,
  `Configure`, `Disable`, `Enable`, `Ensure`, `Gather`, `Install`, `Link`,
  `Load`, `Mask`, `Read`, `Remove`, `Reset`, `Restart`, `Run`, `Schedule`,
  `Set`, `Validate`, `Verify`, and `Write`.
- Make the object a concrete noun phrase that names the managed thing, for
  example `drop-in directory`, `policy files`, `payload sources`, or
  `service facts`.
- Name include wrappers as `Run ... tasks`.
- Handler names must use the same format, and `notify` values must match the
  handler name exactly.
- Keep tags lowercase snake_case.

## Ansible Variable Style

- Prefix public role variables, registered facts, `set_fact` values, and
  non-trivial task-local vars with the role name: `dotfiles_`, `system_`, or
  `browser_policies_`.
- Use lowercase snake_case for Ansible variables. Keep upstream config keys
  unchanged inside setting maps such as SSHD, journald, sysctl, browser policy,
  and VS Code policy dictionaries.
- Prefer concise nouns that describe ownership and shape, for example
  `*_settings`, `*_paths`, `*_dirs`, `*_files`, and `*_enabled`.
- Use explicit `loop_control.loop_var` for every non-trivial loop; avoid
  relying on generic `item` when a meaningful loop variable is possible.
- Keep role input validation in `tasks/validate.yml` when the role has enough
  variables to justify it.

## AI Review Rules

- Review changes against this repo's history: early commits were small and
  fix-heavy, while recent commits moved toward opt-in roles, validation, and
  Conventional Commits. Prefer focused corrections over broad rewrites.
- Treat the default `go-task` path as the highest-risk contract: it must stay
  user-level, local, sudo-free, and limited to `playbook_install.yml`.
- Flag any privileged behavior that leaks into the default dotfiles playbook
  or bypasses the explicit system and browser policy playbooks.
- Flag Ansible tasks that are not idempotent, omit FQCN modules, omit explicit
  modes for managed files, use unguarded shell/command calls, or duplicate
  values that belong in inventory/defaults/vars.
- Flag unprefixed Ansible variables, generic loop variables, or role input
  variables that are missing validation.
- Flag direct edits to supported system main configs when a drop-in path is
  available.
- Flag missing documentation, AGENTS, labeler, Renovate, or validation updates
  when repository layout, commands, automation, or runtime behavior changes.
- Flag non-English repository text, comments, task names, docs, and AI
  instructions unless the content is quoted external output.
- Flag secrets, runtime state, generated test workspaces, copied local
  configs, and over-broad cleanup/removal patterns.

## Documentation And Instruction Sync

- Update `README.md` and the nearest applicable `AGENTS.md` when commands,
  playbooks, roles, validation steps, repository layout, or runtime behavior
  change.
- Update role README files when role variables, managed paths, task flow,
  validation, or rollback behavior changes.
- Update `.github/copilot-instructions.md` and relevant
  `.github/instructions/*.instructions.md` when review rules, repository
  structure, naming style, validation, or automation expectations change.
- Keep AI instructions self-documenting: add new directories, ownership
  boundaries, validation commands, and automation rules in the same change that
  introduces them.
- Remove stale AI instructions when files, roles, workflows, or validation
  paths are removed.
- Keep instruction files concise and non-duplicative; repo-wide rules belong
  in root `AGENTS.md` and `.github/copilot-instructions.md`, while path-local
  rules belong in nested `AGENTS.md` and `.github/instructions/`.
- When adding versioned automation dependencies such as GitHub Actions,
  reusable workflows, Docker images, pre-commit hooks, or future GitLab CI
  includes, ensure Renovate can update them or document why they must be
  updated manually.

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
- Run `go-task verify` for a full local validation pass when Taskfile,
  inventory, playbooks, roles, or repository automation change together.

## Done Criteria

- Applicable local `AGENTS.md` rules were followed.
- Runtime behavior changed only when required by the task.
- The default user-level dotfiles flow remains intact and sudo-free.
- Privileged behavior remains explicit and opt-in.
- Relevant validation commands were run or blockers were stated.
- No secrets or machine-local runtime state were added.
