# Scope

Applies to `roles/dotfiles/`.

This is the default user-level dotfiles role used by `playbook_install.yml`.
Follow the root and `roles/AGENTS.md` rules; the deltas below cover mappings
and state ownership.

## Editing Rules

- Keep symlink behavior driven by `dotfiles_mapping`.
- Keep `payload` values relative to `dotfiles_location`.
- Create mapping parent directories from `dest`; use `dotfiles_directories`
  only for extra directories not implied by mappings.
- Keep cleanup entries in `dotfiles_cleanup_paths`, explicit, and narrow.
- Preserve refusal to replace foreign destination files or symlinks. Treat
  linked payloads and copy-once baselines as separate ownership contracts;
  existing local baseline files must survive subsequent applies.
- Keep managed cron jobs self-contained when writing logs: create the target
  state directory before shell redirection opens the log file.
- Keep input validation in `tasks/validate.yml`.

## Validation

- For runtime role, mapping, cleanup, or payload changes, run
  `go-task dotfiles:check` and the root matrix's applicable static checks.
- Use `go-task test:system` to prove apply behavior in a disposable container;
  applying the role to the developer's home is not a validation prerequisite.
- Documentation-only edits need documentation checks, not apply or convergence.

## Done Criteria

- The default `go-task` flow remains sudo-free.
- Mapping entries are linked; copy-once baselines remain regular local files.
- No secrets, generated state, or local runtime state were added.
