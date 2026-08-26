---
name: validate-dotfiles-change
description: Select and run the minimum validation for a change in this repository. Use when implementing or reviewing dotfiles, Ansible, policy, Neovim, documentation, or automation changes.
---

# Validate a dotfiles change

1. Read the root and nearest `AGENTS.md` for every changed path.
2. Read `docs/adr/0001-validation-strategy.md`.
3. Verify external behavior against the owning primary source or installed
   version. Attach a date or version to facts that can change, and label
   unresolved claims as unverified.
4. Inspect the diff and select the narrowest checks that cover changed behavior.
5. Run those checks and `git diff --check`. Use `go-task verify` only for broad,
   cross-layer changes.
6. Add or update a test or assertion only when behavior or a regression contract
   changed. Prefer an existing smoke, idempotency, schema, or generated-output
   check; do not add tests for unchanged behavior.
7. Report commands, results, and exact blockers. Never substitute a live or
   privileged host for an unavailable container check.
