# dotfiles

User-level role for validating and linking the repository `dotfiles/` payload
into `$HOME`.

This role is the default workflow behind `playbook_install.yml` and `go-task`.
It must stay local, sudo-free, and limited to user-owned paths.

## Variables

Host-specific mappings live in `inventory/host_vars/this_host/dotfiles.yml`.

Core defaults:

| Variable | Purpose |
| -------- | ------- |
| `dotfiles_home` | Destination home directory, normally `ansible_facts.user_dir`. |
| `dotfiles_location` | Repository payload directory used as the symlink source root. |
| `dotfiles_owner` / `dotfiles_group` | Owner and group for created user directories. |
| `dotfiles_directory_mode` | Mode for automatically created user directories. |
| `dotfiles_mapping` | Managed symlink declarations. |
| `dotfiles_directories` | Extra directories not implied by mapping destinations. |
| `dotfiles_cleanup_paths` | Narrow legacy paths removed by the role. |

Each mapping item uses a compact model:

```yaml
dotfiles_mapping:
  - name: bashrc
    payload: .bashrc
    dest: "{{ dotfiles_home }}/.bashrc"
```

`payload` is always relative to `dotfiles_location`; the role computes `src`
at apply time. Parent directories for mapping destinations are derived from
`dest` and created automatically. Use `dotfiles_directories` only for extra
directories that are not implied by a mapping destination.

Use `dotfiles_cleanup_paths` for narrow, explicit legacy path removals.
Public role variables use the `dotfiles_` prefix; loop variables and registered
facts are also role-prefixed to keep validation output clear.

## Role Flow

The role keeps the default install path deterministic:

1. Validate role variables and mapping entries.
2. Verify every mapped payload exists under `dotfiles_location`.
3. Create extra and mapping-derived parent directories.
4. Link managed payloads into `dotfiles_home`.
5. Remove explicit legacy cleanup paths.
6. Manage the Neovim restore cron entry when `crontab` exists.
7. Remove the legacy PAM environment file.

## Validation

```bash
go-task
go-task lint
go-task verify
git diff --check
```
