# Scope

- Applies to files under `dotfiles/`.
- This directory is the declarative payload linked into `$HOME` by
  Ansible.

# Edit Here When

- You are changing a managed dotfile or directory payload.
- You are updating canonical config content that should be symlinked into
  the user home directory.

# Do Not Put Here

- Secrets, tokens, cookies, caches, histories, session state, local
  databases, or other runtime state.
- Browser profiles, SSH private keys, GPG private keys, or machine-local
  credentials.
- Generated output that can be recreated locally.

# Keep In Sync

- Adding a new managed payload file usually also requires updating
  `../inventory/host_vars/this_host.yml`.
- If a file is not added to the mapping, it will not be linked by the
  main playbook.
- Sensitive directories such as `.ssh` or `.gnupg` need explicit directory
  metadata in inventory so modes stay deterministic.

# Validation

- Run `go-task` when testing user-level payload installation.
- Run `go-task lint` for changes that also touch inventory or playbooks.
- Run `uv run yamllint .` when YAML files under `dotfiles/` change and the
  tool is available.
- If you edit Neovim config under `.config/nvim/`, also follow the local
  `AGENTS.md` there and run `go-task test:nvim`.

# Done Means

- The payload is declarative and safe to symlink into `$HOME`.
- Required inventory mapping changes were made.
- No runtime state or secrets were added.
