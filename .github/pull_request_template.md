# Summary

- TBD

# Scope

- [ ] User-level dotfiles only
- [ ] Inventory or Ansible plumbing
- [ ] Opt-in system role
- [ ] Browser or VS Code policies
- [ ] Neovim config
- [ ] CI, release, or repository tooling
- [ ] Documentation or AI instructions

# Validation

- [ ] `git diff --check`
- [ ] `go-task lint`
- [ ] `uv run yamllint .`
- [ ] `go-task verify`
- [ ] `go-task`
- [ ] `go-task docs:nvim-keymaps:check`
- [ ] `go-task test:nvim`
- [ ] `go-task system:check`
- [ ] `go-task test:system`
- [ ] `go-task browser-policies:check`
- [ ] `go-task superlinter` (targeted check when full `go-task verify` was not run)
- [ ] Not applicable, reason:

# Safety

- [ ] Default `go-task` remains user-level and does not require sudo
- [ ] Privileged behavior remains opt-in
- [ ] No secrets, tokens, runtime state, caches, profiles, or generated
      workspaces are committed
- [ ] System config changes prefer drop-ins where supported
- [ ] PAM limits and kernel module options use `limits.d` and `modprobe.d`
      snippets
- [ ] Ansible variables follow role prefixes and settings-map casing rules
- [ ] Role input variables are validated where the role exposes a contract
- [ ] README and nearest `AGENTS.md` files are updated when commands,
      structure, validation, or behavior changes
- [ ] Generated manuals such as `docs/nvim-keymaps.md` are current when their
      source config changes
- [ ] Copilot and `.github/instructions/` rules are updated when review
      expectations change
- [ ] Versioned automation remains covered by Renovate or has an explicit
      manual update reason
- [ ] Rollback path is clear for system-wide changes

# Notes

- TBD
