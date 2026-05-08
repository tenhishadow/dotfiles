# Summary

- TBD

# Scope

- [ ] User-level dotfiles only
- [ ] Inventory or Ansible plumbing
- [ ] Opt-in system role
- [ ] Browser or VS Code policies
- [ ] Neovim config
- [ ] CI, release, or repository tooling

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
- [ ] Rollback path is clear for system-wide changes

# Notes

- TBD
