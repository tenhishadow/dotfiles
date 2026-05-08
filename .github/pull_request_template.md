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
- [ ] `go-task`
- [ ] `go-task test:nvim`
- [ ] `go-task system:check`
- [ ] `go-task test:system`
- [ ] `go-task browser-policies:check`
- [ ] `go-task superlinter`
- [ ] Not applicable, reason:

# Safety

- [ ] Default `go-task` remains user-level and does not require sudo
- [ ] Privileged behavior remains opt-in
- [ ] No secrets, tokens, runtime state, caches, profiles, or generated
      workspaces are committed
- [ ] System config changes prefer drop-ins where supported
- [ ] README and nearest `AGENTS.md` files are updated when commands,
      structure, validation, or behavior changes
- [ ] Versioned automation remains covered by Renovate or has an explicit
      manual update reason
- [ ] Rollback path is clear for system-wide changes

# Notes

- TBD
