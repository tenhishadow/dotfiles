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
- Keep public role input validation in `tasks/validate.yml` when the role has
  a meaningful variable contract.
- Keep tasks small, named, tagged where useful, and easy to review.
- Use handlers for service restarts triggered by config changes.
- Keep templates deterministic and avoid reading unmanaged local state.
- Prefix role variables, registered facts, and task-local vars with the role
  name unless the value is an upstream config key inside a settings map.
- Use explicit `loop_control.loop_var` for loops that read more than a scalar.
- Keep comments, task names, and docs in English.
- Privileged roles must remain opt-in and must not be added to the default
  user-level playbook unless explicitly requested.

## Naming Style

- Name every role task and handler as `<Domain> | <Verb> <object>`.
- Use the repo-wide verb set from the root `AGENTS.md`.
- Name include wrappers as `Run ... tasks`.
- Keep handler names and `notify` values identical.
- Keep tags lowercase snake_case.

## Validation

- Run `go-task lint` for role changes.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.
- Run `go-task verify` when role changes span multiple roles, playbooks,
  inventory, or automation.
- Run role-specific checks from nested `AGENTS.md` files.

## Done Criteria

- The role is idempotent, lint-clean, and reviewable.
- Privileged behavior remains opt-in.
- The default user-level install flow is unchanged unless explicitly required.
