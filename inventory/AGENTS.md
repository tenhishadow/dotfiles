# Scope

Applies to `inventory/` and `inventory/host_vars/`.

This area defines local host data for the dotfiles, system, and browser policy
playbooks.

## Source Of Truth

- `hosts.yml` defines the local `this_host` inventory target.
- `host_vars/this_host.yml` owns dotfile mappings, cleanup actions, browser
  policy overrides, and local system role settings.
- New payload files under `../dotfiles/` must be added to `dotfiles_mapping`
  before the default playbook can link them.
- System role values are used only by `playbook_system.yml`.
- Browser policy values are used only by `playbook_browser_policies.yml`.

## Editing Rules

- Keep paths, modes, owners, and groups explicit.
- Keep cleanup entries narrow, intentional, and reviewable.
- Keep variables declarative; avoid embedding procedural logic in inventory.
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
