# Scope

- Applies to `.test/`.
- This directory contains Neovim smoke-test fixtures and generated test
  workspaces plus system-role container smoke tests.

# Canonical Vs Generated

- Fixture source files such as `.test/nvim/smoke.lua`,
  `.test/nvim/treesitter_install.lua`, and the language sample files are
  canonical test inputs.
- `.test/system/exec.sh` is the Arch Linux container smoke and idempotency
  script used by `go-task test:system`.
- `.test/nvim/.config`, `.test/nvim/.data`, `.test/nvim/.state`, and
  `.test/nvim/.cache` are generated scratch areas for isolated test runs.
- Do not treat generated copies as the source of truth for editor config.

# Validation

```bash
go-task test:nvim
go-task test:system
```

# Done Means

- Fixture changes still support the smoke test.
- Generated test workspace content was not mistaken for canonical config.
