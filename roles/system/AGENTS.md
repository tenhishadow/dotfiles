# Scope

Applies to `roles/system/`.

This is the opt-in Arch Linux workstation system provisioning role.

## Role Flow

Keep the high-level flow predictable:

- Assert supported OS.
- Include distro-specific vars.
- Derive CI, container, and systemd capability guards.
- Install `system_packages` with tag `pkg`.
- Run time and NTP tasks.
- Run common system tasks.
- Run Arch Linux tasks.
- Run Docker tasks only when not in CI and not in a container.
- Run laptop and user-systemd tasks.

## Editing Rules

- Preserve CI and container guards.
- Preserve `ansible_facts` based OS and virtualization checks.
- Preserve `become: true` where system paths or services require privilege.
- Do not move privileged behavior into unguarded shell commands.
- Prefer drop-ins over upstream main-file edits where supported.
- For templates rendered into `/etc`, keep `owner`, `group`, and `mode`
  explicit.
- Keep `backup: true` when a task already uses it.
- Keep handler-driven service restarts.
- Keep task names, comments, templates, and documentation in English.
- Do not change system package lists here; package list rules live in
  `vars/AGENTS.md`.
- Do not commit secrets, private keys, tokens, generated configs, or local
  runtime state.

## Validation

- Run `go-task lint`.
- Run `go-task system:check` for behavior or variable changes.
- Run `go-task test:system` for task, template, or handler changes when
  Docker is available.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.

## Done Criteria

- The role remains lint-clean and guarded for CI and container execution.
- The system playbook is idempotent where covered by the test path.
- The default user-level dotfiles flow is unchanged.
