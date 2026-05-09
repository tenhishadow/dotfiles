# Repository Review Rules

Review this Arch Linux dotfiles and opt-in workstation automation repo for
reliability, security, idempotence, and low maintenance.

## Critical Contracts

- Default `go-task` must remain user-level and sudo-free.
- `playbook_install.yml` must keep `become: false` and must not include
  `roles/system` or `roles/browser_policies`.
- `playbook_install.yml` may include `roles/dotfiles` only.
- Privileged system and browser policy behavior must stay opt-in.
- Reject secrets, private keys, browser profiles, caches, generated test
  workspaces, copied local configs, and machine-local runtime state.

## Ansible Review

- Ansible play, task, and handler names must use
  `<Domain> | <Verb> <object>`; include wrappers use `Run ... tasks`.
- Handler names and `notify` values must match; tags stay lowercase snake_case.
- Role variables, registered facts, and non-trivial task vars use
  `dotfiles_`, `system_`, or `browser_policies_`.
- Non-trivial loops set `loop_control.loop_var`; avoid generic `item`.
- Validate role input variables in `tasks/validate.yml` when they form a real
  contract.
- Keep host vars split under `inventory/host_vars/this_host/`; do not recreate
  a monolithic host vars file.
- Prefer FQCN modules, idempotence, explicit ownership/modes, and handlers.
- Flag shell/command unless it has clear idempotence through
  `changed_when`, `creates`, `removes`, or an equivalent guard.
- Dotfiles mappings must use `name`, relative `payload`, and absolute `dest`;
  the role computes `src` and creates destination parent directories.
- System setting maps should use `system_journald_settings`,
  `system_sshd_settings`, and `system_sysctl_settings`; preserve upstream
  option casing inside those maps.
- Prefer system drop-ins over editing upstream main config files where
  supported.
- PAM limits must use `/etc/security/limits.d/`; kernel module options must use
  `/etc/modprobe.d/`.
- Host sysctl overrides belong in `system_sysctl_settings`; defaults belong in
  `system_sysctl_default_settings`.

## Repository Review

- Docs and nearest `AGENTS.md` files must change with new commands, playbooks,
  roles, validation paths, automation, or runtime behavior.
- For Neovim changes, enforce the structured lazy.nvim layout, deterministic
  `lazy-lock.json`, centralized `lua/config/languages.lua` tool lists, and
  `NVIM_USE_MASON` opt-in behavior. Tree-sitter parser installation must stay
  explicit and skip cleanly when required external tools are unavailable.
  Filetype-lazy plugins must have first-buffer detection in
  `lua/config/filetypes.lua`.
- For Neovim keymap changes, require updates to
  `lua/config/keymaps_spec.lua` and `docs/nvim-keymaps.md`. Keymap docs must
  state the active leader key plainly and pass `go-task docs:nvim-keymaps:check`.
- Check role READMEs, issue forms, and PR templates when their workflows,
  validation, safety rules, managed files, variables, or rollback change.
- Keep repository text, comments, task names, docs, and AI instructions in
  English.
- Keep GitHub Actions least-privilege, deterministic, and Renovate-updateable.
- Keep `.github/labeler.yml`, templates, Renovate, and AI instructions aligned.
- Keep Super-Linter separate from `go-task lint`.

## Suggested Validation

- Ansible, inventory, role, Taskfile, or playbook changes: `go-task lint`.
- YAML-heavy changes: `go-task yamllint`.
- Default dotfiles flow or mappings: `go-task`.
- Neovim config: `go-task test:nvim`; for startup-sensitive changes also run
  `go-task test:nvim:profile`.
- Neovim keymaps: `go-task docs:nvim-keymaps:check`.
- System role: `go-task system:check`; use `go-task test:system` for task,
  template, or handler behavior when Docker is available.
- Browser policies: `go-task browser-policies:check`.
- CI or repo-wide lint behavior: `go-task superlinter` when Docker is
  available.
- Full local validation: `go-task verify`.
