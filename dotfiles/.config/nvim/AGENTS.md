# Scope

Applies only to `dotfiles/.config/nvim/`.

This is the canonical Neovim config. Generated test copies under `.test/` are
not source of truth.

## Structure

- `init.lua` is the minimal entry point.
- `lua/setup.lua` bootstraps lazy.nvim and loads plugin specs.
- `lua/config/` contains core editor behavior.
- `lua/plugins/` and `lua/kickstart/plugins/` contain plugin definitions.
- `lua/utils/` contains small reusable helpers.
- `lazy-lock.json` pins plugin versions and should change only
  intentionally.

## Editing Rules

- Keep startup flow simple and predictable.
- Keep plugin definitions grouped by domain.
- Keep LSP setup executable-aware and avoid noisy failures when optional
  external binaries are missing.
- Keep comments, descriptions, and labels in English.
- Do not edit generated `.test/nvim/.config/nvim` copies as canonical config.

## Validation

```bash
go-task test:nvim
```

This test uses isolated `.test/nvim` XDG paths and is the required smoke test
for Neovim changes.

## Done Criteria

- Neovim still boots through the expected layers.
- Plugin and LSP changes remain reproducible.
- `go-task test:nvim` passes or any blocker is stated precisely.
