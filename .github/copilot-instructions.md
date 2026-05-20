# Repository Review Rules

Review this dotfiles repo for reliability, security, idempotence, and low
maintenance. Former `ans-workstation` automation is opt-in.

## Contracts

- Default `go-task` stays user-level and sudo-free; `playbook_install.yml`
  keeps `become: false` and only includes `roles/dotfiles`.
- Privileged system and browser/Thunderbird/VS Code policies stay opt-in.
- Docs must not put privileged config in default `go-task` or present personal
  workstation values as a generic hardening benchmark.
- Reject secrets, private keys, browser/mail profiles, caches, kubeconfigs,
  cloud credentials, AI/MCP state, test workspaces, local configs, and runtime state.

## Ansible

- Names use `<Domain> | <Verb> <object>`; include wrappers use `Run ... tasks`;
  handler names and `notify` match; tags stay lowercase snake_case.
- Role variables, registered facts, and non-trivial task vars use `dotfiles_`,
  `system_`, or `browser_policies_`; non-trivial loops set `loop_control.loop_var`.
- Validate role inputs in `tasks/validate.yml`; keep host vars split under
  `inventory/host_vars/this_host/`.
- Prefer FQCN modules, idempotence, explicit ownership/modes, and handlers.
- Flag shell/command without `changed_when`, `creates`, `removes`, or an
  equivalent idempotence guard.
- Dotfiles mappings use `name`, relative `payload`, and absolute `dest`.
- System setting maps use `system_journald_settings`, `system_sshd_settings`,
  and `system_sysctl_settings`; preserve upstream key casing.
- Prefer drop-ins over editing upstream main configs where supported.
- Verify policy/privacy keys upstream; do not guess AI-client, browser,
  package-manager, or developer-tool settings.
- Use `/etc/security/limits.d/` for PAM limits and `/etc/modprobe.d/` for
  kernel module options.
- Put host sysctl overrides in `system_sysctl_settings`; defaults in
  `system_sysctl_default_settings`.

## Repository Review

- Docs and nearest `AGENTS.md` files change with new commands, roles,
  validation paths, automation, or runtime behavior.
- For Neovim changes, enforce structured lazy.nvim layout, deterministic
  `lazy-lock.json`, centralized tool lists, `NVIM_USE_MASON` opt-in behavior,
  explicit Tree-sitter installs, first-buffer filetype detection, and
  non-mutating save behavior. Lint may run on save; formatting and whitespace
  stripping stay manual.
- Neovim keymap changes update `lua/config/keymaps_spec.lua` and
  `docs/nvim-keymaps.md`; docs state the leader key plainly and pass
  `go-task docs:nvim-keymaps:check`.
- Check role READMEs, issue forms, and PR templates when workflows,
  validation, safety rules, managed files, variables, or rollback change.
- Keep architecture, adoption, security, and migration docs aligned when system
  behavior or consolidation wording changes.
- Keep repository text, comments, task names, docs, and AI instructions English.
- Keep GitHub Actions least-privilege, deterministic, and Renovate-managed.
- Keep Renovate scoped to real dependency surfaces; `.test/` fixtures are not
  Renovate dependencies.
- Leave `pyproject.toml` constraints unpinned unless requested; `uv.lock`
  records resolved versions.
- Keep labeler, templates, Renovate, and AI instructions aligned.
- Keep Super-Linter separate from `go-task lint`.

## Suggested Validation

- Ansible, inventory, role, Taskfile, playbook changes: `go-task lint`.
- YAML-heavy changes: `go-task yamllint`.
- Default dotfiles flow or mappings: `go-task dotfiles:check`; use `go-task`
  when apply must be exercised.
- Neovim config: `go-task test:nvim`; startup-sensitive changes also run
  `go-task test:nvim:profile`.
- Neovim keymaps: `go-task docs:nvim-keymaps:check`.
- System role: `go-task system:check`; task/template/handler changes also use
  `go-task test:system` when Docker is available.
- Browser policies: `go-task browser-policies:check`.
- CI or repo-wide lint behavior: `go-task superlinter` when Docker is available.
- Full validation: `go-task verify`.
