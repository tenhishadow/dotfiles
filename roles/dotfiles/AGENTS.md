# Scope

Applies to `roles/dotfiles/`.

This is the default user-level dotfiles role used by `playbook_install.yml`.

## Editing Rules

- Keep this role local, user-level, and sudo-free.
- Do not add `become: true`.
- Do not manage system paths, browser policies, packages, or services here.
- Keep symlink behavior driven by `dotfiles_mapping`.
- Keep `payload` values relative to `dotfiles_location`.
- Create mapping parent directories from `dest`; use `dotfiles_directories`
  only for extra directories not implied by mappings.
- Keep cleanup entries in `dotfiles_cleanup_paths`, explicit, and narrow.
- Keep input validation in `tasks/validate.yml`.
- Keep task names, comments, and docs in English.

## Validation

- Run `go-task` for role, mapping, cleanup, or payload changes.
- Run `go-task lint`.
- Run `go-task verify` when this role changes together with inventory,
  playbooks, Taskfile, or documentation.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.

## Done Criteria

- The default `go-task` flow remains sudo-free.
- Managed files are linked from the repository payload.
- No secrets, generated state, or local runtime state were added.
