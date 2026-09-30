# Scope

Applies to `dotfiles/`.

This directory is the canonical user-level payload linked or seeded into
`$HOME` by `playbook_install.yml`. The root `AGENTS.md` owns repository-wide
security, language, and execution-scope rules.

## Edit Here When

- Changing a managed dotfile or directory payload.
- Updating canonical user configuration that should be symlinked into
  `$HOME`.
- Adding fixtures that are part of the user's desired home configuration.

## Do Not Put Here

- Generated test copies, caches, and application runtime state.
- Generated XDG desktop state such as `.config/user-dirs.dirs`; let
  `xdg-user-dirs-update` own the local file.
- System-wide `/etc` configuration; use an opt-in playbook or role instead.

## Mapping Rules

- Add a mapping in `inventory/host_vars/this_host/dotfiles.yml` for each new
  destination. Files inside an already linked directory need no separate
  entry.
- Use `dotfiles_mapping` for symlinks and `dotfiles_baseline_files` for
  copy-once configurations rewritten by applications. Existing baselines
  remain local regular files; a runtime writer must not alter repository
  content through a symlink.
- Mapping entries use `name`, `payload` relative to `dotfiles_location`, and
  absolute `dest`; `roles/dotfiles` computes the source path.
- Parent directories for mapping destinations are created automatically. Use
  `dotfiles_directories` only for extra directories not implied by mappings.
- Skills under `dotfiles/.agents/skills/` are managed user-level payloads for
  other repositories. Repository workflows belong in root `.agents/skills/`.

## Owner Decisions

- `dotfiles/.ssh/config` contains explicitly chosen owner policy. Preserve its
  settings unless the owner explicitly requests an SSH configuration change.
  Do not revise them during hardening, modernization, cleanup, or AI review,
  and do not weaken their contract tests to substitute an agent's preferences.
  The config is the canonical source for these values; the native SSH tests
  enforce the selected defaults and host-specific override precedence.

## Validation

Use the root validation matrix for the changed payload type. Run
`go-task dotfiles:check` when runtime payload or destination behavior changes;
documentation-only edits need documentation checks. Neovim-specific checks
live in `dotfiles/.config/nvim/AGENTS.md`.

## Done Criteria

- Payload uses the appropriate symlink or copy-once ownership contract.
- Required inventory mapping changes were made.
- No runtime state, secrets, or generated artifacts were added.
