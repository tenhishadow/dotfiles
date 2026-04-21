# Scope

- Applies to `inventory/` and `inventory/host_vars/`.
- This area defines what the main playbook manages on `this_host`.

# Source Of Truth

- `host_vars/this_host.yml` is the source of truth for dotfiles mappings
  and cleanup actions.
- New payload files under `../dotfiles/` must be added to the mapping to
  take effect.
- The default inventory target is local `this_host`.

# Editing Rules

- Keep paths, modes, owners, and groups explicit and deterministic.
- Keep cleanup entries narrow, intentional, and documented by context.
- Do not put secrets in host vars.
- Do not add broad or destructive cleanup patterns.

# Validation

- Run `go-task lint` for inventory or playbook-adjacent changes.
- Run `uv run yamllint .` when YAML changes and the tool is available.
- Run `go-task` only when you intentionally want to exercise the local
  user-level install flow.

# Done Means

- The inventory still targets `this_host` locally.
- Mapping and cleanup behavior is explicit and reviewable.
- No secrets or accidental destructive actions were introduced.
