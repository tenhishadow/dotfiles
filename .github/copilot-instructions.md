# Repository Review Rules

Review this repository as Arch Linux dotfiles plus opt-in workstation
automation. Optimize for reliability, security, idempotence, and low
maintenance.

## Critical Contracts

- The default `go-task` path must remain user-level and sudo-free.
- `playbook_install.yml` must keep `become: false` and must not include
  `roles/system` or `roles/browser_policies`.
- `roles/dotfiles` is the only role allowed in `playbook_install.yml`, and it
  must stay user-level and sudo-free.
- Privileged system and browser policy behavior must stay behind explicit
  opt-in playbooks/tasks.
- Do not allow secrets, tokens, private keys, browser profiles, caches,
  generated test workspaces, copied local configs, or machine-local runtime
  state into git.

## Ansible Review

- All Ansible play, task, and handler names must use
  `<Domain> | <Verb> <object>`.
- Include wrappers must be named `Run ... tasks`.
- Handler names and `notify` values must match exactly.
- Tags should remain lowercase snake_case.
- Role variables, registered facts, and non-trivial task-local vars should use
  the role prefix: `dotfiles_`, `system_`, or `browser_policies_`.
- Non-trivial loops should set `loop_control.loop_var`; flag generic `item`
  when a meaningful variable name would make validation and review clearer.
- Role input variables should be covered by `tasks/validate.yml` when the role
  owns a real variable contract.
- Keep host vars split under `inventory/host_vars/this_host/`; do not recreate
  a monolithic host vars file.
- Prefer FQCN modules, idempotent modules, explicit file ownership/modes, and
  handler-driven service restarts.
- Flag shell/command usage unless it has clear idempotence through
  `changed_when`, `creates`, `removes`, or an equivalent guard.
- Keep duplicated literals in inventory, role defaults, or role vars.
- Dotfiles mappings must use `name`, relative `payload`, and absolute `dest`;
  the role computes `src` and creates destination parent directories.
- System setting maps should use `system_journald_settings`,
  `system_sshd_settings`, and `system_sysctl_settings`; preserve upstream
  option casing inside those maps.
- Prefer system drop-ins over editing upstream main config files where
  supported.

## Repository Review

- Check that docs and nearest `AGENTS.md` files change with new commands,
  playbooks, roles, validation paths, automation, or runtime behavior.
- Check role README files when role variables, managed files, task flow,
  validation, or rollback behavior changes.
- Check issue forms and PR templates when supported workflows, validation
  commands, or safety constraints change.
- Keep repository text, comments, task names, docs, and AI instructions in
  English.
- Keep GitHub Actions least-privilege, deterministic, and Renovate-updateable.
- Do not move Super-Linter into `go-task lint`; keep it as the separate
  repository-wide lint path.
- Keep `.github/labeler.yml`, issue templates, PR template, Renovate, and AI
  instructions aligned with the current repo structure.

## Suggested Validation

- Ansible, inventory, role, Taskfile, or playbook changes: `go-task lint`.
- YAML-heavy changes: `go-task yamllint`.
- Default dotfiles flow or mappings: `go-task`.
- System role: `go-task system:check`; use `go-task test:system` for task,
  template, or handler behavior when Docker is available.
- Browser policies: `go-task browser-policies:check`.
- CI or repo-wide lint behavior: `go-task superlinter` when Docker is
  available.
- Full local validation: `go-task verify`.
