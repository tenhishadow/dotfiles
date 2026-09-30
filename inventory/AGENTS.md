# Scope

Applies to `inventory/` and `inventory/host_vars/`.

This area defines local host data for the dotfiles, system, and browser policy
playbooks.

The root `AGENTS.md` owns role naming, security, and execution-scope rules.

## Source Of Truth

- `hosts.yml` defines the local `this_host` inventory target.
- `host_vars/this_host/dotfiles.yml` owns dotfile mappings and cleanup.
- `host_vars/this_host/browser_policies.yml` owns browser, Thunderbird, and VS
  Code policy overrides.
- `host_vars/this_host/system.yml` owns non-security system role values.
- `host_vars/this_host/security.yml` owns SSHD, sysctl, and limits
  security-sensitive workstation values.
- New destinations require a `dotfiles_mapping` or `dotfiles_baseline_files`
  entry; files inside an already mapped directory inherit its symlink.
- System role values are used only by `playbook_system.yml`.
- Browser, Thunderbird, and VS Code policy values are used only by
  `playbook_browser_policies.yml`.
- Do not recreate monolithic `host_vars/this_host.yml`; keep ownership split
  across the directory files above.

## Editing Rules

- Keep paths, modes, owners, and groups explicit.
- Keep cleanup entries narrow, intentional, and reviewable.
- Keep variables declarative; avoid embedding procedural logic in inventory.
- Keep `dotfiles_mapping` entries in `name`, `payload`, `dest` form.
- Keep dotfiles `payload` values relative to `dotfiles_location`.
- Use copy-once baselines for application-rewritten configurations so the
  application cannot write runtime state through a repository symlink.
- Do not add generated XDG desktop state such as `user-dirs.dirs` to
  `dotfiles_mapping`; `xdg-user-dirs-update` owns that local file.

## Validation

- Use the root matrix for changed inventory behavior; documentation-only edits
  need documentation checks.
- Run `go-task lint` for inventory data changes.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.
- Run `go-task dotfiles:check` for mapping or cleanup changes that affect the default
  user-level install flow.
- Run `go-task system:check` for system role variable changes.
- Run `go-task browser-policies:check` for browser policy variable changes.

## Done Criteria

- Inventory still targets local `this_host`.
- Mapping, cleanup, and override behavior is explicit and reviewable.
- The default workflow remains user-level and sudo-free.
- No secrets or accidental destructive actions were introduced.
