# Scope

Applies to `roles/system/`.

This is the opt-in Arch Linux workstation system provisioning role.
It contains the system automation consolidated from the former
`tenhishadow/ans-workstation` repository.
The root and `roles/AGENTS.md` supply shared Ansible and execution-scope rules.

## Role Flow

Keep the high-level flow predictable:

- Assert supported OS.
- Include distro-specific vars.
- Derive CI, container, virtual machine, systemd, time-backend, and AUR
  capability guards.
- Validate role variables.
- Install `system_packages` with tag `pkg`.
- Run AUR helper tasks with tag `aur` only when guarded as safe.
- Run timezone tasks and select Chrony for virtual machines or timesyncd for
  physical hosts when systemd is manageable.
- Run locale, console, login, limits, cron, and sysctl tasks.
- Run the shared drop-in flow (`sys-dropins.yml` over `system_dropins`:
  journald and timesyncd) and the SSHD tasks.
- Run Arch Linux tasks and opt-in periodic TRIM timer management.
- Run Docker tasks only when not in CI and not in a container; keep overlay
  module options behind `system_docker_overlay_options_enabled`.
- Run laptop, opt-in TuneD, and user-systemd tasks.

## Editing Rules

- Preserve `ansible_facts` based OS and virtualization checks.
- Keep time-daemon selection in `tasks/time-backend.yml`: virtual machines use
  Chrony, physical hosts use timesyncd, and container/CI guards select neither.
- Unmask the selected time service before enabling it, and never include that
  service in the computed conflict list.
- Preserve an existing enabled, active, or starting synchronization waiter by
  enabling the selected daemon's native waiter for the next boot. Do not start
  a blocking waiter during apply or add one when neither waiter was enabled,
  active, or starting; verify VM reboot behavior.
- Skip timezone changes as well as daemon management in containers and CI.
  Never substitute ntpd for Chrony on VMs. Disabling a host-class backend must
  select no fallback daemon.
- Keep Chrony configuration validation ahead of daemon changes. Preserve the
  refusal to overwrite unmanaged systemd unit files while creating conflict
  masks; a disabled feature flag does not undo existing service state.
- Keep TuneD profile state unchanged on an idle apply. Profile transitions and
  battery behavior require physical-host verification, not container claims.
- Preserve `become: true` where system paths or services require privilege.
- Do not move privileged behavior into unguarded shell commands.
- Add a new reset-style systemd drop-in as a `system_dropins` descriptor
  rendered by `sys-dropins.yml`, not as a new parallel task file; sshd stays separate
  because its verify-include/validate ordering is not shared.
- Keep role-owned sysctl defaults in `system_sysctl_default_settings`; use
  `system_sysctl_settings` only for host-specific additions and overrides.
- Manage PAM limits through `/etc/security/limits.d/`; do not edit
  `/etc/security/limits.conf`.
- Manage kernel module options through `/etc/modprobe.d/` snippets.
- Keep `backup: true` when a task already uses it.
- Follow `roles/system/vars/AGENTS.md` when changing package manifests.

## Validation

- Use the root matrix for static checks. Documentation-only changes need
  documentation checks, not system check mode or container convergence.
- Run `go-task system:check` for behavior or variable changes.
- Run `go-task test:system` for package manifest, task, template, or handler
  changes when Docker is available.

## Done Criteria

- The role remains lint-clean and guarded for CI and container execution.
- The system playbook is idempotent where covered by the test path.
- The default user-level dotfiles flow is unchanged.
