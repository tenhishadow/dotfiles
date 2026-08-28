# Repository

Personal Arch Linux dotfiles and workstation automation repository managed with
Ansible, `uv`, and `go-task`.

## Architecture

`docs/architecture.md` is the canonical layer model and safety-boundary
description; this section is the agent-facing file-location map.

- `dotfiles/` contains the canonical user-level payload linked into `$HOME`.
- `playbook_install.yml` is the default user-level install playbook.
- `playbook_system.yml` is the explicit privileged workstation playbook.
- `playbook_browser_policies.yml` is the explicit privileged browser policy
  playbook.
- `go-task all` is the explicit privileged aggregate apply target for user
  dotfiles, system workstation, and browser policy layers.
- `inventory/host_vars/this_host/` is the local source of truth for dotfiles
  mappings, cleanup, browser policy overrides, and system role values.
- `roles/dotfiles/` contains the default user-level dotfiles workflow.
- `roles/system/` contains opt-in Arch Linux workstation provisioning
  consolidated from the former `tenhishadow/ans-workstation` repository.
- `roles/browser_policies/` contains opt-in browser, Thunderbird, and VS Code
  policy management.
- `docs/` contains architecture, adoption, security, migration, and generated
  operator manuals.

## Instruction Scope

- The nearest `AGENTS.md` applies.
- Nested `AGENTS.md` files add local rules and should not duplicate this file
  wholesale.
- Check local instructions before editing (`go-task docs:agents` regenerates
  this list; `go-task docs:agents:check` fails if it is stale):
  <!-- BEGIN GENERATED: nested-agents (go-task docs:agents) -->
  - `.github/AGENTS.md`
  - `.test/AGENTS.md`
  - `dotfiles/.config/nvim/AGENTS.md`
  - `dotfiles/AGENTS.md`
  - `inventory/AGENTS.md`
  - `roles/AGENTS.md`
  - `roles/dotfiles/AGENTS.md`
  - `roles/system/AGENTS.md`
  - `roles/system/vars/AGENTS.md`
  <!-- END GENERATED: nested-agents -->

## Hard Rules

- Keep the default `go-task` path user-level, local, sudo-free, and limited to
  `playbook_install.yml` with `roles/dotfiles` only; do not add `become: true`
  or the system and browser policy roles to that playbook.
- Treat `go-task all` and system or browser policy playbooks and tasks as
  explicit privileged opt-ins, never as the default workflow.
- Do not present personal workstation security values as a generic hardening
  benchmark.
- Prefer service drop-ins over editing upstream main config files where
  supported.
- Keep changes deterministic, narrow, reviewable, and idempotent.
- Keep repository text, comments, task names, documentation, and AI
  instructions in English (enforced by `go-task lint:english`).
- Do not commit secrets, tokens, cookies, browser or mail profiles, session
  state, local databases, caches, private keys, kubeconfigs, cloud
  credentials, AI account state, MCP credentials, generated test workspaces, or
  copied runtime configs.
- Manage privacy and policy values only through documented upstream config or
  enterprise policy keys. Do not invent settings for AI clients, browsers,
  package managers, or developer tools.

## Engineering Rules

- Prefer boring, upstream-compatible Ansible over custom shell.
- Use FQCN modules such as `ansible.builtin.file`.
- Use explicit ownership and mode for managed files, especially under `/etc`.
- Keep variables in inventory, role defaults, or role vars instead of
  duplicating literals.
- Keep package lists, policy target lists, and user-level privacy configs
  declarative.
- Keep AUR helper/package management in `roles/system` task files tagged `aur`
  and guarded from check-mode, CI, and container execution.
- Use handlers for service restarts when template or config changes require
  them.
- Preserve CI and container guards for privileged system behavior.
- Do not broaden cleanup/removal patterns without an explicit requirement.
- Keep Python tool dependencies in `pyproject.toml` unpinned unless the user
  explicitly asks for a constraint. Let `uv.lock` carry resolved versions.

## Ansible Naming Style

- Use one format for all Ansible play, task, and handler names:
  `<Domain> | <Verb> <object>`. The format and exact `notify`/handler matching
  are enforced by `go-task lint:ansible-semantics`.
- Keep domains short, verbs imperative, objects concrete, and upstream product
  casing intact (`systemd`, `SSHD`, `VS Code`, `Neovim`).
- Name include wrappers as `Run ... tasks`.
- Keep tags lowercase snake_case.

## Ansible Variable Style

- Prefix public role variables, registered facts, `set_fact` values, and
  non-trivial task-local vars with the role name: `dotfiles_`, `system_`, or
  `browser_policies_`, in lowercase snake_case. Both rules are enforced by
  ansible-lint (`var-naming`).
- Keep upstream config keys unchanged inside setting maps such as SSHD,
  journald, sysctl, browser policy, and VS Code policy dictionaries.
- Prefer concise nouns that describe ownership and shape, for example
  `*_settings`, `*_paths`, `*_dirs`, `*_files`, and `*_enabled`.
- Use explicit `loop_control.loop_var` for every non-trivial loop; avoid
  relying on generic `item` when a meaningful loop variable is possible.
- Keep role input validation in `tasks/validate.yml` when the role has enough
  variables to justify it.

## AI Review Rules

- Treat the default-workflow boundary in Hard Rules as the highest-risk
  contract.
- Prefer focused corrections over broad rewrites and compare behavioral changes
  with the repository's opt-in, validation, and rollback contracts.
- Flag missing documentation, AGENTS, labeler, Renovate, or validation updates
  when repository layout, commands, automation, or runtime behavior changes.
- Flag Neovim keymap changes that do not update
  `dotfiles/.config/nvim/lua/config/keymaps_spec.lua`,
  `docs/nvim-keymaps.md`, and the keymap documentation check.

## Documentation And Instruction Sync

This layer is single-source and self-checked. Edit the one canonical home for a
rule; do not fan the same rule out into every file.

- Repo-wide rules live in this root `AGENTS.md`. The agent ownership map (the
  nested-`AGENTS.md` list above) is generated: run `go-task docs:agents` after
  adding or removing a nested `AGENTS.md`, and `go-task docs:agents:check`
  fails on a stale map.
- The `go-task` command catalog lives in the README `Common Tasks` table.
  Reference commands by name elsewhere; never repeat the table.
- Mechanical rules are enforced, not restated: the `<Domain> | <Verb> <object>`
  naming and `notify`/handler contract by `go-task lint:ansible-semantics`,
  variable naming by ansible-lint, and English-only text by
  `go-task lint:english`. Other files point to the rule and its check instead
  of rewriting it.
- `go-task docs:instructions:check` fails when any doc references a missing
  `go-task` target, role, playbook, or repository path, so a rename cannot
  leave a stale instruction behind. This replaces manual cross-file fan-out:
  remove the source rule once and the checks catch every dangling reference.
- Nested `AGENTS.md` and `.github/instructions/*` carry only path-local rules
  and reference this file for repo-wide rules.
  `.github/copilot-instructions.md` is the condensed Copilot review surface and
  stays under 4,000 characters.
- `CLAUDE.md` and `GEMINI.md` import this file. Repository skills under
  `.agents/skills/` contain task-specific workflows, not copies of always-on
  rules.
- Update role README files, and the architecture, adoption, security, and
  migration/history docs, when role contracts or system-layer behavior change.
- Keep `.ruff.toml` and `.github/linters/.ruff.toml` synchronized because
  local Ruff and Super-Linter read different config paths.
- Keep `.github/linters/.python-lint` as the shared Pylint configuration for
  `go-task lint:python` and the early Python CI job. Super-Linter does not own
  project-aware Pylint or Mypy execution.
- Keep Markdown rules in `.github/linters/.markdown-lint.yml`; local
  `markdownlint-cli2`, pre-commit, and Super-Linter share that file. Fix
  violations instead of adding file ignores or inline rule disables.
- When adding versioned automation dependencies such as GitHub Actions,
  reusable workflows, Docker images, or pre-commit hooks, ensure Renovate can
  update them or document why they must be updated manually.

## Commit Rules

- Use Conventional Commits when a commit is requested.
- Keep commit messages compatible with `.commitlintrc.yaml`.
- Keep commits scoped to the requested change.
- Do not push unless explicitly requested.
- Do not include unrelated dirty worktree changes.

## Validation Matrix

The README `Common Tasks` table is the authoritative `go-task` command
reference; the rules below map change types to those commands.

- Always run `git diff --check` before finishing non-trivial changes.
- Run `go-task dotfiles:check` for user dotfiles, symlink mappings, cleanup,
  or default install flow changes.
- Run `go-task lint` for Ansible, inventory, role, Taskfile, or playbook
  changes.
- Run `go-task lint:markdown` for Markdown, AGENTS, skill, or template changes.
- Run `go-task lint:python` for repository Python changes.
- Run `go-task test:agent-tooling` for managed Codex profiles, hooks, package
  manifests, or lockfiles.
- Run `go-task test:python` for repository Python contract or regression tests.
- Run `uv run yamllint .` or `go-task yamllint` for YAML-heavy changes.
- Run `go-task vint` for Vimscript payloads or Vint configuration changes.
- Run `go-task docs:nvim-keymaps:check` for Neovim keymap changes.
- Run `go-task test:nvim` for Neovim config changes.
- Run `go-task test:nvim:profile` for startup-sensitive Neovim changes.
- Run `go-task system:check` for system role changes.
- Run `go-task test:system` for dotfiles, system, or policy apply behavior when
  Docker is available. It checks observable state and zero-change second runs
  for all three playbooks.
- Run `go-task browser-policies:check` for browser policy role or policy
  inventory changes.
- Run `go-task superlinter` for focused CI or repository-wide lint changes
  when Docker is available.
- Run `go-task verify:fast` for broad static validation without Docker or
  managed-host writes.
- Run `go-task verify` for a full local validation pass when Taskfile,
  inventory, playbooks, roles, or repository automation change together.
  It adds isolated Neovim checks, Arch convergence, and Super-Linter, and
  requires a running Docker daemon without applying the local workstation.

## Done Criteria

- Applicable local `AGENTS.md` rules were followed.
- Runtime behavior changed only when required by the task.
- The Hard Rules and execution-layer boundaries remain intact.
- Relevant validation commands were run or blockers were stated.
- No secrets or machine-local runtime state were added.
