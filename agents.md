# How this repository works (dotfiles)

## Purpose and scope
This repository is a self-contained dotfiles installer that uses Ansible to place symlinks into the current user's home directory. The canonical files live under `dotfiles/`, and the playbook builds a deterministic, repeatable setup for shell, editor, terminal, and CLI tooling. The default workflow is designed for a local workstation (no SSH, no sudo by default).

## Primary entry points
- `Taskfile.yml` is the main task runner. Running `go-task` (default task) installs Python deps via `uv`, installs Ansible Galaxy collections, then runs the playbook with Mitogen enabled.
- `playbook_install.yml` is the single Ansible playbook that applies all dotfile changes.
- `inventory/hosts.yml` declares a single local host (`this_host`).
- `inventory/host_vars/this_host.yml` defines all dotfile mappings and cleanup actions.

## Task flow (Taskfile.yml)
- `deps-os` installs OS-level tools (Arch Linux: `uv` and `git`). It runs without sudo if possible, otherwise retries with sudo.
- `deps-python` runs `uv sync` in locked mode (no dev deps, no project install) to create the Ansible runtime.
- `deps-galaxy` installs Ansible collections from `requirements.yml`.
- `default` runs the playbook via `uv run ansible-playbook playbook_install.yml`, with Mitogen enabled by setting `ANSIBLE_STRATEGY=serverscom.mitogen.mitogen_linear`.
- `lint` runs `ansible-lint` inside the `uv` environment.
- `test:nvim` runs the playbook and then performs Neovim health checks and Lazy plugin restore.

Key dependency sources:
- `pyproject.toml` defines Python dependencies: `ansible`, `ansible-lint`, `mitogen`, `jmespath`.
- `uv.lock` pins Python versions and the local package version.
- `requirements.yml` installs the Mitogen collection.

## Ansible configuration (ansible.cfg)
- Inventory is fixed to `./inventory` and uses the YAML inventory plugin.
- Retry files are disabled (`retry_files_enabled = False`).
- Python interpreter selection is set to `auto_silent`.
- Warnings are left enabled for visibility.

## Ansible execution model (playbook_install.yml)
- Runs locally (`connection: local`), with `become: false`.
- `gather_facts: true` so it can use `ansible_facts.user_dir`, `real_user_id`, etc.
- Expects `dotfiles_mapping` to exist; it fails fast if missing.

### Core tasks
1) **Directory preparation**
   - For every mapping entry with `dir_path`/`dir_mode`/`dir_owner`/`dir_group`, it creates the directory with explicit permissions.
   - This is how sensitive directories like `~/.ssh` and `~/.gnupg` are created with restrictive modes.
2) **Symlink creation**
   - Uses the Ansible `file` module with `state: link` and `force: true` for each mapping entry.
   - This overwrites existing files/links at the destination with the repo's dotfiles.
3) **Cleanup**
   - Removes legacy paths listed in `dotfiles_cleanup` (e.g., old Neovim locations).
4) **Cron jobs**
   - A daily cron runs `nvim --headless "+Lazy! restore"` to keep Neovim plugins consistent.
   - An hourly cron runs `git pull` inside `~/.dotfiles`.
5) **Migration**
   - Removes `~/.pam_environment` to enforce the move to `~/.config/environment.d`.

### Tags
- Many file/link tasks are tagged `configs`, so you can limit execution to config-related tasks if needed.

## Inventory + variables (inventory/host_vars/this_host.yml)
- `dotfiles_location` is `{{ playbook_dir }}/dotfiles`, making the repo itself the source of truth.
- `dotfiles_dir_mode` defaults to `u=rwx,g=,o=`.
- `dotfiles_mapping` is the authoritative map of symlinks. It includes:
  - Shell (`.bashrc`, `.bash_profile`), editor configs, system configs, and full directories (`.config/nvim/lua`).
  - Explicit directory creation with owner/group for `~/.gnupg`, `~/.ssh`, `~/.config/kitty`, `~/.config/htop`, etc.
  - Dual mapping of `.yamllint` (both `~/.yamllint` and `~/.config/yamllint/config`).
- `dotfiles_cleanup` removes legacy Neovim paths and old config locations.
Note: Only items in `dotfiles_mapping` are linked; new files in `dotfiles/` must be added there to take effect.

## Dotfiles payload (dotfiles/)
The `dotfiles/` directory is the payload that the playbook links into `$HOME`.

### Shell
- `.bash_profile` simply sources `.bashrc`.
- `.bashrc`:
  - History configuration (append mode, timestamps, large history sizes).
  - Utility functions (git status prompt helper, AWS/Azure helpers, recording, disk checks).
  - Aliases for common tools (kubectl, git, terraform/terragrunt formatting, system cleanup).
  - Uses `starship` if available, otherwise falls back to a custom multi-line prompt that includes git status.
  - Environment configuration for editor, GPG, LESS colors, and PATH extensions.
  - Completion setup for HashiCorp tools, GitHub CLI, AWS CLI, kubectl, docker, helm, fzf, Kitty shell integration, and more.

### Git
- `.gitconfig` contains performance tweaks (commitGraph, untrackedCache), useful aliases, diff/merge preferences, color settings, and a project-specific include (`~/projects/.gitconfig`).
- `.gitignore` is the global ignore list.

### Terminal + prompt
- `~/.config/kitty/kitty.conf` defines the Kitty terminal configuration, fonts, scrollback, and includes `theme.conf`.
- `~/.config/starship.toml` defines the Starship prompt format (git status, username/host, directory, duration, python venv).

### Security and authentication
- `~/.gnupg/gpg.conf` and `gpg-agent.conf` are provided and linked with restrictive directory permissions.
- `~/.ssh/config` sets global SSH defaults (agent forwarding, disabled strict host checking, cipher/KEX restrictions) and includes `config.d/*` and `conf.d/*`.
- `~/.config/environment.d/99-dotfiles.conf` sets `SSH_AUTH_SOCK` for systemd user environments.

### Editors
- **Neovim** (`~/.config/nvim`): modern Lua-based config with lazy.nvim plugin management.
- **Vim** (`~/.vimrc`): legacy configuration using vim-plug, largely mirroring the Neovim plugin set and options.

### Miscellaneous
- `~/.config/htop/htoprc` for htop layout.
- `~/.config/user-dirs.dirs` for XDG user directories.
- `.editorconfig`, `.pylintrc`, `.yamllint` for consistent formatting and linting.
- `.curlrc`, `.wgetrc`, `.screenrc`, `.mplayer/config` for CLI tool behavior.

## Neovim architecture (dotfiles/.config/nvim)
### Boot flow
`init.lua` is intentionally minimal and loads:
1) `config.options`, `config.keymaps`, `config.autocmds`
2) `setup` (lazy.nvim bootstrap + plugin spec)
3) `ft` (custom filetype detection)
4) `fold` (folding defaults)
5) `lsp` (LSP setup)
6) Optional `custom` overrides (if present)

### Plugin manager (setup.lua)
- Bootstraps `lazy.nvim` if missing.
- Loads two plugin trees:
  - `kickstart.plugins` (baseline plugin set)
  - `plugins` (repo-specific plugins, split by domain)
- Enables background update checking and change detection.
- Uses `lazy-lock.json` to pin plugin versions.

### LSP layer (lua/lsp.lua)
- Supports both new (Neovim 0.11+) and legacy LSP APIs.
- Builds capabilities from `blink.cmp` when present, otherwise from `cmp_nvim_lsp`.
- Centralized diagnostics setup (signs, virtual text off, rounded borders).
- `on_attach` sets LSP keymaps and enables inlay hints only for whitelisted server+filetype pairs.
- Server enablement is gated on executable presence (`has_any`), so only installed language servers are configured.
- Uses SchemaStore (`schemastore.nvim`) for JSON/YAML schemas when available.
- Handles TS server renames (`tsserver` vs `ts_ls`) based on runtime.

### LSP tooling installation (lua/plugins/lsp.lua)
- Uses `mason.nvim`, `mason-lspconfig`, and `mason-tool-installer`.
- `mason-lspconfig` installs a curated list of servers and leaves enablement to `lua/lsp.lua`.
- `mason-tool-installer` installs a large set of CLI tools (formatters, linters, scanners) on startup.

### Formatting and linting
- `plugins/format.lua` configures `conform.nvim` with format-on-save and per-filetype formatters.
- `kickstart/plugins/lint.lua` configures `nvim-lint` and only enables linters that exist in `$PATH`.

### Syntax and filetypes
- `plugins/treesitter.lua` installs parsers for core languages; auto-install is disabled for reproducibility.
- `ft.lua` forces Ansible, Fastlane, Terragrunt, and YAML filetypes based on path patterns.
- `fold.lua` uses syntax folding by default; YAML uses marker-based folding.

### UI and workflow
- Themes: `gruvbox` is the primary theme; `molokai` and `tender` are alternatives.
- UI tools include `lightline`, `fzf.vim`, `neo-tree`, `which-key`, `vimwiki`, `gitsigns`, and DAP tooling.

## Vim (legacy) configuration
- `.vimrc` bootstraps `vim-plug`, installs a similar plugin set, and sets consistent folding, filetypes, and keymaps.
- It includes fallback logic to install plugins on first run.

## Automation and release management
- `release-please-config.json` updates versions in `pyproject.toml` and `uv.lock` when releasing.
- `renovate.json` manages dependency updates.
- `CHANGELOG.md` is auto-maintained via release tooling.

## Operational notes and side effects
- Symlinks are **forced**, so existing files at the destination are replaced.
- Cron jobs are installed only if `cron` is available (errors are ignored otherwise).
- Neovim runs can trigger large tool installations via Mason on first use.
- The repo is optimized for Arch Linux defaults (pacman in `deps-os`).

## Common workflows
- Install/refresh: `go-task` (runs deps + playbook).
- Lint Ansible: `task lint`.
- Clean local caches: `task clear`.
- Refresh Neovim plugins and health (plus smoke tests): `task test:nvim`.

## Tests and validation
Required:
- Neovim config validation: `go-task test:nvim` (treat as the required test for all Neovim-related changes).
  - Runs a headless smoke suite in `.test/nvim/smoke.lua` that checks filetype detection, LSP attach (when binaries exist), and basic format/lint hooks.
  - Test fixtures live under `.test/nvim/` and are read by the smoke suite (keep fixtures in sync with `.test/nvim/smoke.lua`).
