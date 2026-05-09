# Scope

Applies only to `dotfiles/.config/nvim/`.

This is the canonical Neovim config. Generated test copies under `.test/` are
not source of truth.

## Structure

- `init.lua` is the minimal entry point.
- `lua/config/lazy.lua` bootstraps lazy.nvim and loads plugin specs.
- `lua/config/` contains core editor behavior.
- `lua/config/filetypes.lua` contains plugin-independent filetype detection
  used by filetype-lazy plugin specs.
- `lua/config/keymaps_spec.lua` is the canonical inventory for user-facing
  keymaps, leader keys, which-key groups, and generated keymap documentation.
- `lua/config/languages.lua` is the shared language/tool inventory for
  Tree-sitter parsers and install requirements, LSP, Mason, formatters, and
  linters.
- `lua/plugins/` contains all lazy.nvim plugin definitions.
- `lua/dotfiles/health.lua` contains `:checkhealth dotfiles`.
- `lua/utils/` contains small reusable helpers.
- `lazy-lock.json` pins plugin versions and should change only
  intentionally.

## Editing Rules

- Keep startup flow simple and predictable.
- Keep the config structured like upstream lazy.nvim guidance: core settings in
  `lua/config/`, plugin specs in `lua/plugins/`, and `require("lazy").setup`
  called once from `lua/config/lazy.lua`.
- Keep lazy.nvim bootstrap deterministic: when `lazy-lock.json` pins
  `lazy.nvim`, the bootstrap checkout must honor that exact commit.
- Keep plugin definitions grouped by domain and avoid reintroducing copied
  `kickstart.nvim` layout or comments.
- Prefer lazy.nvim `opts` over hand-written `config` when a plugin supports a
  standard `setup(opts)` call.
- Add language/tool names once in `lua/config/languages.lua` when the same
  value is needed by LSP, Mason, formatters, linters, or tests.
- Add user-facing keymaps once in `lua/config/keymaps_spec.lua`, then consume
  that inventory from runtime config. Do not hardcode keymap descriptions in
  plugin specs when the keymap should appear in `docs/nvim-keymaps.md`.
- Keep the generated keymap manual current by running
  `go-task docs:nvim-keymaps` after user-facing keymap changes.
- Keep first-buffer filetype detection in `lua/config/filetypes.lua`; do not
  rely on a lazy-loaded plugin's `ftdetect` file for filetypes that trigger
  that same plugin.
- Gate plugins by minimum Neovim version when upstream requires it. The core
  config must not fail on old Debian Neovim; modern plugin/LSP features may be
  disabled there.
- Preserve LSP compatibility for both Neovim 0.11+ `vim.lsp.config` and the
  Neovim 0.10 `nvim-lspconfig` setup API.
- Keep Tree-sitter explicit and quiet: do not enable automatic parser installs
  at startup, keep parser install requirements in `lua/config/languages.lua`,
  and make tests skip parser installation when required external tools are
  missing.
- Keep cold installs deterministic: `Lazy restore` must not update
  `lazy-lock.json`, Mason is opt-in via `NVIM_USE_MASON`, and blink.cmp must
  not require Rust or a prebuilt binary download by default.
- Keep LSP setup executable-aware and avoid noisy failures when optional
  external binaries are missing.
- Keep comments, descriptions, and labels in English.
- Do not edit generated `.test/nvim/.config/nvim` copies as canonical config.

## Validation

```bash
go-task test:nvim
```

This test uses isolated `.test/nvim` XDG paths and is the required smoke test
for Neovim changes. It must also prove that a clean `Lazy! restore` does not
modify `lazy-lock.json`.

Run `go-task test:nvim:profile` for startup-sensitive changes. It runs the
smoke test first, then reports startup time and loaded plugin count.

Run `go-task docs:nvim-keymaps:check` for keymap changes. It verifies that
`docs/nvim-keymaps.md` matches `lua/config/keymaps_spec.lua`.

## Done Criteria

- Neovim still boots through the expected layers.
- Plugin and LSP changes remain reproducible.
- No duplicated plugin families are introduced unless there is an explicit
  reason documented in the plugin spec.
- User-facing keymaps are documented in `docs/nvim-keymaps.md` with the
  current leader key written plainly.
- `go-task test:nvim` passes or any blocker is stated precisely.
