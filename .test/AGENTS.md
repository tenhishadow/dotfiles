# Scope

Applies to `.test/`.

This directory contains canonical smoke-test fixtures and generated local test
workspaces.

## Canonical Files

- `.test/nvim/smoke.lua`
- `.test/nvim/compat.lua`
- `.test/nvim/treesitter_install.lua`
- `.test/nvim/keymap_docs.lua`
- `.test/nvim/mason_tools.lua`
- `.test/nvim/*` language sample fixtures
- `.test/system/exec.sh`

`.test/system/exec.sh` is the Arch Linux container smoke and idempotency script
used by `go-task test:system`.

## Generated Files

These paths are scratch state created by test runs and must not be treated as
source of truth:

- `.test/nvim/.config`
- `.test/nvim/.data`
- `.test/nvim/.state`
- `.test/nvim/.cache`

## Editing Rules

- Keep fixtures minimal and deterministic.
- Keep Neovim smoke fixture directories aligned with the `name` values in
  `.test/nvim/smoke.lua`.
- Keep generated workspaces out of git.
- Keep Neovim test language lists sourced from the canonical config when
  possible, especially `config.languages`.
- Keep Tree-sitter parser installation optional in the test sandbox and skip
  cleanly when required external tools are missing.
- Keep shell scripts robust with safe flags where practical.
- Keep comments, sample text, and documentation in English.

## Validation

```bash
go-task test:nvim
go-task test:nvim:compat
go-task test:nvim:mason-tools
go-task docs:nvim-keymaps:check
go-task test:system
```

Run the test that matches the changed fixture area.

## Done Criteria

- Fixture changes still support the smoke tests.
- Generated test workspace content was not mistaken for canonical config.
- No local runtime state was committed.
