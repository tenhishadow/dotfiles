# Scope

Applies to Ansible roles under `roles/`.

The root `AGENTS.md` owns module, naming, security, and execution-scope rules.

## Editing Rules

- Use `command` or `shell` only when there is no cleaner module and declare
  `changed_when` or `creates`/`removes` behavior explicitly.
- Use explicit modes as quoted strings, for example `"0644"`.
- Keep defaults in `defaults/main.yml`.
- Keep OS-specific constants and package manifests in `vars/`.
- Keep templates deterministic and avoid reading unmanaged local state.
- Keep selected tags complete: input validation and required variables must
  still run when an operator selects only one feature.
- Keep feature flags distinct from removal state. Document when disabling a
  flag only skips management and leaves previously applied state in place.

## Validation

Use the root validation matrix and the role-specific checks in nested
`AGENTS.md` files for implementation changes. Documentation-only role edits
need documentation checks, not container convergence or an aggregate run.

## Done Criteria

- The role is idempotent, lint-clean, and reviewable.
- Privileged behavior remains opt-in.
- The default user-level install flow preserves the root execution contract.
