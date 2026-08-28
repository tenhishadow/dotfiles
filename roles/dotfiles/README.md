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
| `dotfiles_baseline_files` | Copy-once files that applications or hosts may mutate. |
| `dotfiles_directories` | Extra directories not implied by mapping destinations. |
| `dotfiles_cleanup_paths` | Narrow legacy paths removed by the role. |
| `dotfiles_nvim_restore_cron_enabled` | Explicit opt-in for the Neovim restore cron job. |
| `dotfiles_nvim_state_dir` | User-owned state directory for Neovim cron logs and lock file. |
| `dotfiles_cron_path` | Explicit PATH used by managed cron commands. |
| `dotfiles_nvim_restore_cron_job` | Headless Neovim lazy restore command. |

Each mapping item uses a compact model:

```yaml
dotfiles_mapping:
  - name: bashrc
    payload: .bashrc
    dest: "{{ dotfiles_home }}/.bashrc"
```

`payload` is always relative to `dotfiles_location`; the role computes `src`
at apply time. Parent directories for mapping destinations are derived from
`dest` and created automatically. `dotfiles_baseline_files` uses the same item
shape plus an optional `mode`; it copies missing files without overwriting local
changes. A legacy symlink is migrated only when it points to that baseline's
repository payload. Use `dotfiles_directories` only for extra directories that
are not implied by a managed destination.

Use `dotfiles_cleanup_paths` for narrow, explicit legacy symlink removals. The
role removes only symlinks whose normalized targets are beneath
`dotfiles_location`; it preserves user-owned symlinks, regular files, and
directories so applying this host inventory on another account cannot erase
unrelated local data.
Public role variables use the `dotfiles_` prefix; loop variables and registered
facts are also role-prefixed to keep validation output clear.

## Managed Tool Configs

This role now includes safe user-level configs for tools already represented in
the workstation package manifest, including Gemini CLI, K9s, Git Delta,
Terraform CLI, bat, ripgrep, btop, direnv, npm, Yarn, and pip.

Codex ships a secret-free base-configuration example, task-focused profiles,
a deterministic command-safety hook, and an opt-in Ponytail skill. The example
MCP surface is limited to Context7 and the official OpenAI documentation server.
The live `~/.codex/config.toml` is deliberately not linked because Codex writes
project and hook trust state into it; bootstrap a new host from
`dotfiles/.codex/config.example.toml`, then keep its live config local and
owner-only. Grafana and Playwright are disabled unless their dedicated profile
is selected; GitHub writes require the explicit, non-destructive
`github-write` profile. Ponytail is linked to `~/.agents/skills/ponytail`, the
cross-agent user skill location. Its local policy defaults to lite and prevents
implicit Codex invocation.
The `codex` launcher prefers the exact dependency graph installed from the
checked-in npm lock, falls back to an existing system Codex, and applies an
owner-only umask before startup so newly created histories and databases do not
inherit a permissive workstation default.
Context7 and Playwright resolve from checked-in npm lockfiles and never download
packages while Codex is starting. After applying the dotfiles on a new machine,
run `go-task codex:install` once to populate the CLI and MCP runtime directories.

These files are normal dotfiles under `$HOME` or XDG config paths. They do not
include kubeconfigs, tokens, cloud credentials, Terraform registry credentials,
npm tokens, pip indexes, AI account state, MCP credentials, local histories, or
runtime profiles.

Codex authentication, conversation and memory state, hook trust state, MCP
credentials, and the Grafana URL and service-account token file are deliberately
local. The hook does not read workspace files or inject extra model context.
It blocks direct Bash references to local `.env`, Kubernetes config, GnuPG
private keys, the Grafana token-file variable, and non-public SSH paths while
allowing managed SSH and GnuPG config and public `.pub` keys.
Review new or changed hooks with `/hooks` before trusting them.

K9s is configured with `readOnly: true`, so the managed default is intentionally
read-only. Git Delta is configured as the Git pager and assumes `delta` is
installed. npm uses `audit=false` as a privacy-first default; run `npm audit`
explicitly in project workflows when needed.

Review `inventory/host_vars/this_host/dotfiles.yml` before applying on another
account because the role can replace managed destinations with symlinks.

The Neovim restore cron command is opt-in and is scheduled only when `crontab`,
`flock`, and Neovim are executable at the declared paths. If the feature is
disabled or its runtime dependencies disappear, the role removes its cron
entry whenever `crontab` is available. It uses a Lua
`pcall(require, "lazy")` wrapper and `NVIM_USE_MASON=off`, creates the state
directory before opening its log, and uses `flock` to prevent overlapping
background restores.

## Role Flow

The role keeps the default install path deterministic:

1. Validate role variables and mapping entries.
2. Verify every linked and baseline payload exists under `dotfiles_location`.
3. Create extra and managed-file parent directories.
4. Link managed payloads into `dotfiles_home`.
5. Migrate repository-linked baselines, then seed missing baseline files.
6. Remove explicit legacy cleanup symlinks.
7. Detect cron and Neovim restore capabilities.
8. Reconcile the Neovim cron entry and remove legacy cron entries whenever
   `crontab` is available.
9. Remove the legacy PAM environment file.

## Validation

```bash
go-task
go-task lint
go-task verify
git diff --check
```
