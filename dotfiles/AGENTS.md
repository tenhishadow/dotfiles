# Scope

Applies to `dotfiles/`.

This directory is the canonical user-level payload linked into `$HOME` by
`playbook_install.yml`.

## Edit Here When

- Changing a managed dotfile or directory payload.
- Updating canonical user configuration that should be symlinked into
  `$HOME`.
- Adding fixtures that are part of the user's desired home configuration.

## Do Not Put Here

- Secrets, tokens, cookies, histories, session state, local databases, or
  caches.
- Browser profiles, SSH private keys, GPG private keys, or machine-local
  credentials.
- Generated output that can be recreated locally.
- System-wide `/etc` configuration; use an opt-in playbook or role instead.

## Mapping Rules

- New managed payload files usually require a matching entry in
  `../inventory/host_vars/this_host.yml`.
- If a file is not in `dotfiles_mapping`, the default playbook will not link
  it.
- Sensitive directories such as `.ssh` and `.gnupg` need explicit directory
  metadata so modes stay deterministic.
- Keep payload text, comments, and user-facing messages in English.

## Validation

- Run `go-task` for user-level payload or mapping changes.
- Run `go-task lint` for changes that also touch inventory or playbooks.
- Run `uv run yamllint .` or `go-task yamllint` for YAML changes.
- For Neovim config under `.config/nvim/`, also follow the local
  `AGENTS.md` and run `go-task test:nvim`.

## Done Criteria

- Payload remains declarative and safe to symlink into `$HOME`.
- Required inventory mapping changes were made.
- No runtime state, secrets, or generated artifacts were added.
