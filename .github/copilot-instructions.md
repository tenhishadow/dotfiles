# Repository Review Rules

Review this personal Arch Linux dotfiles repo for reliability, security,
idempotence, and low maintenance. Former `ans-workstation` automation is
opt-in here.

## Critical Contracts

- Default `go-task` must remain user-level and sudo-free.
- `playbook_install.yml` keeps `become: false` and may include
  `roles/dotfiles` only.
- Privileged system and browser/Thunderbird/VS Code policy behavior must stay
  opt-in.
- Docs must not imply privileged configuration is part of default `go-task`.
- Security wording must not present personal workstation values as a generic
  hardening benchmark.
- Reject secrets, private keys, browser or mail profiles, caches, kubeconfigs,
  cloud credentials, AI account state, MCP credentials, generated test
  workspaces, local configs, and machine-local runtime state.

## Ansible Review

- Ansible play, task, and handler names must use
  `<Domain> | <Verb> <object>`; include wrappers use `Run ... tasks`.
- Handler names and `notify` values must match; tags stay lowercase snake_case.
- Role variables, registered facts, and non-trivial task vars use
  `dotfiles_`, `system_`, or `browser_policies_`.
- Non-trivial loops set `loop_control.loop_var`; avoid generic `item`.
- Validate role inputs in `tasks/validate.yml` when they form a contract.
- Keep host vars split under `inventory/host_vars/this_host/`.
- Prefer FQCN modules, idempotence, explicit ownership/modes, and handlers.
- Flag shell/command unless it has clear idempotence through
  `changed_when`, `creates`, `removes`, or an equivalent guard.
- Dotfiles mappings use `name`, relative `payload`, and absolute `dest`.
- System setting maps use `system_journald_settings`,
  `system_sshd_settings`, and `system_sysctl_settings`; preserve upstream key
  casing.
- Prefer system drop-ins over editing upstream main config files where
  supported.
- Policy and privacy config keys must be verified against upstream
  documentation. Do not guess AI-client, browser, package-manager, or developer
  tool settings.
- PAM limits must use `/etc/security/limits.d/`; kernel module options must use
  `/etc/modprobe.d/`.
- Host sysctl overrides belong in `system_sysctl_settings`; defaults belong in
  `system_sysctl_default_settings`.

## Repository Review

- Docs and nearest `AGENTS.md` files must change with new commands, roles,
  validation paths, automation, or runtime behavior.
- For Neovim changes, enforce structured lazy.nvim layout, deterministic
  `lazy-lock.json`, centralized tool lists, `NVIM_USE_MASON` opt-in behavior,
  explicit Tree-sitter installs, and first-buffer filetype detection.
- For Neovim keymap changes, require updates to
  `lua/config/keymaps_spec.lua` and `docs/nvim-keymaps.md`. Keymap docs must
  state the active leader key plainly and pass `go-task docs:nvim-keymaps:check`.
- Check role READMEs, issue forms, and PR templates when their workflows,
  validation, safety rules, managed files, variables, or rollback change.
- Keep architecture, adoption, security, and migration/history docs aligned
  when system-layer behavior or consolidation wording changes.
- Keep repository text, comments, task names, docs, and AI instructions in
  English.
- Keep GitHub Actions least-privilege, deterministic, and Renovate-updateable.
- Keep Renovate scoped to real dependency surfaces; `.test/` fixtures are not
  Renovate-managed dependencies.
- Leave `pyproject.toml` dependency constraints unpinned unless requested;
  `uv.lock` records resolved versions.
- Keep labeler, templates, Renovate, and AI instructions aligned.
- Keep Super-Linter separate from `go-task lint`.

## Suggested Validation

- Ansible, inventory, role, Taskfile, or playbook changes: `go-task lint`.
- YAML-heavy changes: `go-task yamllint`.
- Default dotfiles flow or mappings: `go-task dotfiles:check`; use `go-task`
  when the apply path must be exercised.
- Neovim config: `go-task test:nvim`; for startup-sensitive changes also run
  `go-task test:nvim:profile`.
- Neovim keymaps: `go-task docs:nvim-keymaps:check`.
- System role: `go-task system:check`; use `go-task test:system` for task,
  template, or handler changes when Docker is available.
- Browser, Thunderbird, or VS Code policies: `go-task browser-policies:check`.
- CI or repo-wide lint behavior: `go-task superlinter` when Docker is
  available.
- Full local validation: `go-task verify`.
