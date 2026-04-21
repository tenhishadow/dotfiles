# Scope

- Applies only to `dotfiles/.config/nvim/`.
- This is the canonical Neovim config, not the generated test copy under
  `.test/`.

# Structure

- `init.lua` is the minimal entry point.
- It loads core config, lazy.nvim setup, filetype and fold helpers, LSP,
  and optional `custom` overrides.
- `lua/setup.lua` bootstraps lazy.nvim and loads plugin specs from
  `kickstart.plugins` and `plugins`.
- `lazy-lock.json` pins plugin versions and should only change
  intentionally.

# Editing Rules

- Keep boot flow simple and predictable.
- Keep plugin definitions split by domain rather than piling everything
  into one file.
- LSP setup must stay executable-aware and avoid noisy startup failures
  when external binaries are missing.
- Do not treat `.test/nvim/.config/nvim` as canonical config.

# Validation

```bash
go-task test:nvim
```

- This uses isolated `.test/nvim` XDG paths and is the required smoke test
  for Neovim changes.

# Done Means

- Neovim still boots through the expected layers.
- Plugin and LSP changes remain reproducible.
- `go-task test:nvim` passes or any blocker is stated precisely.
