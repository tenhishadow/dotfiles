# Scope

- Applies to Ansible roles under `roles/`.

# Editing Rules

- Use FQCN modules such as `ansible.builtin.copy`.
- Prefer idempotent modules.
- Avoid `command` and `shell` unless there is no cleaner option.
- Use explicit modes as strings such as `"0644"`.
- Keep defaults in `defaults/main.yml`.
- Keep tasks small, tagged, and easy to review.
- Privileged roles must be opt-in and must not be added to the default
  user-level playbook unless explicitly requested.

# Validation

- Run `go-task lint`.
- Run `uv run yamllint .` when YAML changes and the tool is available.

# Done Means

- The role is idempotent and lintable.
- Privileged behavior remains opt-in.
- The default user-level install flow is unchanged.
