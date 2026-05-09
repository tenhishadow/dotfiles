# Scope

Applies to `inventory/` and `inventory/host_vars/`.

This area defines local host data for the dotfiles, system, and browser policy
playbooks.

## Source Of Truth

- `hosts.yml` defines the local `this_host` inventory target.
- `host_vars/this_host/dotfiles.yml` owns dotfile mappings and cleanup.
- `host_vars/this_host/browser_policies.yml` owns browser policy overrides.
- `host_vars/this_host/system.yml` owns non-security system role values.
- `host_vars/this_host/security.yml` owns SSHD, sysctl, and limits hardening
  values.
- New payload files under `../dotfiles/` must be added to
  `dotfiles_mapping` before the default playbook can link them.
- System role values are used only by `playbook_system.yml`.
- Browser policy values are used only by `playbook_browser_policies.yml`.
- Do not recreate monolithic `host_vars/this_host.yml`; keep ownership split
  across the directory files above.

## Editing Rules

- Keep paths, modes, owners, and groups explicit.
- Keep cleanup entries narrow, intentional, and reviewable.
- Keep variables declarative; avoid embedding procedural logic in inventory.
- Keep host variables role-prefixed: `dotfiles_*`, `system_*`, or
  `browser_policies_*`.
- Preserve upstream option names inside settings maps such as
  `system_sshd_settings`, `system_journald_settings`,
  `system_sysctl_settings`, and browser policy dictionaries.
- Keep `dotfiles_mapping` entries in `name`, `payload`, `dest` form.
- Keep dotfiles `payload` values relative to `dotfiles_location`.
- Do not put secrets or machine-local runtime state in host vars.
- Do not add broad globs or destructive cleanup patterns.
- Do not make the default dotfiles playbook privileged through inventory.
- Keep comments and variable descriptions in English.

## Validation

- Run `go-task lint` for inventory changes.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.
- Run `go-task` for mapping or cleanup changes that affect the default
  user-level install flow.
- Run `go-task system:check` for system role variable changes.
- Run `go-task browser-policies:check` for browser policy variable changes.

## Done Criteria

- Inventory still targets local `this_host`.
- Mapping, cleanup, and override behavior is explicit and reviewable.
- The default workflow remains user-level and sudo-free.
- No secrets or accidental destructive actions were introduced.
