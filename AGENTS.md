# Repository

- Arch Linux dotfiles repository managed with Ansible and `go-task`.
- `dotfiles/` is the payload directory that gets linked into `$HOME`.
- The default workflow is local and user-level.
- `playbook_install.yml` is the main dotfiles playbook.
- The default playbook runs with `connection: local` and `become: false`.
- `playbook_system.yml` is the opt-in privileged Arch Linux system playbook.
- `roles/system/` contains the migrated workstation system provisioning role.

# Main Entry Points

- `README.md`: install overview and clone/bootstrap example.
- `Taskfile.yml`: primary task runner and validation entry point.
- `playbook_install.yml`: main user-level install/refresh flow.
- `playbook_system.yml`: opt-in system-level workstation flow.
- `inventory/hosts.yml`: local `this_host` inventory target.
- `inventory/host_vars/this_host.yml`: source of truth for mappings and
  cleanup plus local system role settings.
- `ansible.cfg`: Ansible execution defaults for this repo.

# How Instructions Apply

- `AGENTS.md` is the canonical instruction format in this repo.
- The nearest `AGENTS.md` applies for files in its directory tree.
- Nested `AGENTS.md` files add local rules; they should not repeat this
  file.
- Check local instructions before editing in:
  - `dotfiles/AGENTS.md`
  - `dotfiles/.config/nvim/AGENTS.md`
  - `inventory/AGENTS.md`
  - `.github/AGENTS.md`
  - `.test/AGENTS.md`
  - `roles/AGENTS.md` when `roles/` exists

# Global Hard Rules

- Preserve the existing default dotfiles workflow.
- Do not make the default `go-task` flow require sudo for dotfile apply.
- Do not add `become: true` to `playbook_install.yml`.
- Keep privileged or system-wide changes opt-in through a separate
  playbook/task.
- Do not add `roles/system` to `playbook_install.yml`.
- Do not make the default `go-task` target depend on `system`,
  `system:check`, or `test:system`.
- Do not change runtime behavior unless the task explicitly requires it.
- Keep changes deterministic, narrow, and easy to validate.
- Do not commit secrets, tokens, cookies, browser profiles, session state,
  local databases, caches, or other machine-local runtime state.
- Do not commit generated test workspaces or copied configs.

# Validation Commands

- `git diff --check`
  - Run before finishing any non-trivial change.
- `go-task`
  - Run when changing the default user-level install flow, symlink mapping,
    or payload that should be applied into `$HOME`.
- `go-task lint`
  - Run for Ansible, inventory, Taskfile, or playbook changes.
- `go-task system:check`
  - Run for system role changes before applying them locally.
- `go-task test:system`
  - Run for system role task/template/handler behavior changes.
  - Docker is required.
- `uv run yamllint .`
  - Run for YAML-heavy changes when `yamllint` is available in the existing
    toolchain.
- `go-task superlinter`
  - Run for repo-wide lint or CI-related changes.
  - Docker is required.
- `go-task test:nvim`
  - Run for Neovim config changes.
  - This uses isolated `.test/nvim` XDG paths and should be treated as the
    required smoke test for Neovim work.

# Workflow Notes

- `uv` manages the Python and Ansible environment.
- `deps-galaxy` installs required Ansible collections from
  `requirements.yml`.
- `task lint` intentionally runs only `ansible-lint`.
- `task superlinter` is intentionally separate from `task lint`.
- Keep YAML, Ansible, and task changes aligned with `.yamllint`,
  `.ansible-lint.yml`, and `.editorconfig`.

# Done Means

- The nearest applicable `AGENTS.md` rules were followed.
- Relevant validation commands were run for the files you changed.
- The default user-level dotfiles flow is still intact.
- Any privileged behavior remains explicit and opt-in.
- No secrets or runtime state were added to the repo.
