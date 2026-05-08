# AGENTS.md

## Scope

- This file applies to `roles/system/`.
- This is the main Arch Linux system provisioning role.

## Role Flow

- Keep the high-level task order intact:
- assert supported OS
- include distro vars
- install `system_packages` with tag `pkg`
- run common system tasks
- run Arch Linux tasks
- run Docker tasks when not in Docker and not in CI
- run laptop and user-systemd tasks

## Local Rules

- Preserve existing CI and container guards.
- Preserve `ansible_facts` based OS and virtualization checks.
- Preserve `become: true` where system paths or services require privilege.
- Do not move privileged behavior into unguarded shell commands.
- For templates rendered into `/etc`, keep `owner`, `group`, and `mode`
  explicit.
- Keep `backup: true` when the existing task already uses it.
- Keep handler-driven restarts where they already exist.
- Do not change system package lists here. Package list rules live in
  `vars/AGENTS.md`.
- Do not commit secrets, private keys, tokens, generated configs, or local
  runtime state.

## Validate

- Run `go-task lint`.
- For task, template, or handler behavior changes, also run
  `go-task test:system` when Docker is available.

## Done Means

- The role stays lint-clean, guarded for CI and container execution, and
  idempotent where covered by the existing test path.
