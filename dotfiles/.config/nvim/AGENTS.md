# Scope

Applies only to `dotfiles/.config/nvim/`.

This is the canonical Neovim config. Generated test copies under `.test/` are
not source of truth. The root and `dotfiles/AGENTS.md` own shared rules.

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
- `lua/config/quickfix.lua` contains manual validation commands. These commands
  must stay opt-in and must not run scanners automatically on save.
- `lua/plugins/` contains all lazy.nvim plugin definitions.
- `lua/dotfiles/health.lua` contains `:checkhealth dotfiles`.
- `lua/utils/` contains small reusable helpers.
- `lazy-lock.json` pins plugin versions and should change only
  intentionally.

## Editing Rules

- Keep the config structured like upstream lazy.nvim guidance: core settings in
  `lua/config/`, plugin specs in `lua/plugins/`, and `require("lazy").setup`
  called once from `lua/config/lazy.lua`.
- Keep lazy.nvim bootstrap deterministic: when `lazy-lock.json` pins
  `lazy.nvim`, the bootstrap checkout must honor that exact commit.
- Keep plugin definitions grouped by domain.
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
- Keep `nvim-lspconfig` and Mason LSP integration on the Neovim 0.11.3+
  `vim.lsp.config` path required by the current config. Recheck upstream
  requirements when updating the lock; older Neovim must still load the core
  config without the plugin layer.
- Keep Kubernetes, Helm, GitOps, CI, Docker Compose, Terraform/OpenTofu, and
  policy-language filetype routing in `lua/config/filetypes.lua`; keep their
  tools and schema data in `lua/config/languages.lua`.
- Keep Tree-sitter explicit and quiet: do not enable automatic parser installs
  at startup, keep parser install requirements in `lua/config/languages.lua`,
  and let ordinary local tests skip parser installation when required external
  tools are missing. CI uses required mode and must fail instead of skipping.
- Keep cold installs deterministic: `Lazy restore` must not update
  `lazy-lock.json`, Mason is opt-in via `NVIM_USE_MASON`, and blink.cmp must
  not require Rust or a prebuilt binary download by default.
- Keep blink.cmp on its configured stable v1 line unless a major upgrade is
  explicitly in scope.
- Keep `lua/config/languages.lua` Mason lists limited to package names that
  exist in the Mason registry. External tools such as `kubeconform` and
  `kustomize` belong in health/manual command inventories unless Mason adds
  packages for them.
- Keep automatic linting lightweight and file-local. Project-wide or security
  scanners belong in manual commands or manual linter inventories, not in
  save-time auto lint.
- Keep save-time behavior non-mutating. Do not enable format-on-save,
  format-after-save, or whitespace stripping on save; formatters are for
  explicit manual use only.
- Manual buffer formatting must operate only on that buffer. Disable formatter
  project globs where needed, and preserve error callbacks so failures remain
  observable instead of silently reporting success.
- Use canonical `conform.nvim` formatter names and `nvim-lint` linter names in
  `lua/config/languages.lua`; `go-task test:nvim` must catch unknown formatter
  or linter inventory entries.
- Keep LSP setup executable-aware and avoid noisy failures when optional
  external binaries are missing.

## Validation

For runtime configuration or lockfile changes, run `go-task test:nvim`. It
uses isolated `.test/nvim` HOME and XDG paths and must prove that a clean
`Lazy! restore` does not modify `lazy-lock.json`. Documentation-only edits
need the root matrix's documentation checks.

Run `go-task test:nvim:profile` for startup-sensitive changes. It runs the
smoke test first, then reports startup time and loaded plugin count.

Run `go-task test:nvim:compat` for changes that affect startup, core config,
filetype routing, health checks, or manual commands. It simulates the
old-Neovim core-only path by disabling the plugin layer.
This checks the fallback path on the installed binary; it does not prove
compatibility with an older Neovim version unless that version is actually run.

Run `go-task docs:nvim-keymaps:check` for keymap changes. It verifies that
`docs/nvim-keymaps.md` matches `lua/config/keymaps_spec.lua`.

Run `go-task test:nvim:mason-tools` after changing Mason tool inventories. It
verifies sorted, unique Mason package names against the pinned, network-free
registry snapshot.

## Done Criteria

- Neovim still boots through the expected layers.
- Plugin and LSP changes remain reproducible.
- No duplicated plugin families are introduced unless there is an explicit
  reason documented in the plugin spec.
- User-facing keymaps are documented in `docs/nvim-keymaps.md` with the
  current leader key written plainly.
- Applicable checks pass or any blocker is stated precisely.
