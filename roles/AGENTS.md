# Scope

Applies to Ansible roles under `roles/`.

## Editing Rules

- Use FQCN modules such as `ansible.builtin.copy`.
- Prefer idempotent Ansible modules over `command` or `shell`.
- Use `command` or `shell` only when there is no cleaner module and declare
  `changed_when` or `creates`/`removes` behavior explicitly.
- Use explicit modes as quoted strings, for example `"0644"`.
- Keep defaults in `defaults/main.yml`.
- Keep OS-specific constants and package manifests in `vars/`.
- Keep tasks small, named, tagged where useful, and easy to review.
- Use handlers for service restarts triggered by config changes.
- Keep templates deterministic and avoid reading unmanaged local state.
- Keep comments, task names, and docs in English.
- Privileged roles must remain opt-in and must not be added to the default
  user-level playbook unless explicitly requested.

## Validation

- Run `go-task lint` for role changes.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.
- Run role-specific checks from nested `AGENTS.md` files.

## Done Criteria

- The role is idempotent, lint-clean, and reviewable.
- Privileged behavior remains opt-in.
- The default user-level install flow is unchanged unless explicitly required.
