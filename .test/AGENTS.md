# Scope

- Applies to `.test/`.
- This directory contains Neovim smoke-test fixtures and generated test
  workspaces.

# Canonical Vs Generated

- Fixture source files such as `.test/nvim/smoke.lua`,
  `.test/nvim/treesitter_install.lua`, and the language sample files are
  canonical test inputs.
- `.test/nvim/.config`, `.test/nvim/.data`, `.test/nvim/.state`, and
  `.test/nvim/.cache` are generated scratch areas for isolated test runs.
- Do not treat generated copies as the source of truth for editor config.

# Validation

```bash
go-task test:nvim
```

# Done Means

- Fixture changes still support the smoke test.
- Generated test workspace content was not mistaken for canonical config.
