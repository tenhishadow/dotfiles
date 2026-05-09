---
applyTo: "dotfiles/.config/nvim/**/*,.test/nvim/**/*"
---

# Neovim Review Instructions

- Preserve a structured lazy.nvim layout: `init.lua` loads core config,
  `lua/config/lazy.lua` owns bootstrap/setup, and `lua/plugins/` owns plugin
  specs.
- Keep `lazy-lock.json` deterministic. Cold `Lazy restore` must not rewrite
  it, and the bootstrap must honor the pinned `lazy.nvim` commit.
- Do not reintroduce a copied `kickstart.nvim` plugin tree. Keep plugin specs
  grouped by domain under `lua/plugins/`.
- Prefer `opts` over custom `config` when lazy.nvim can call
  `require(MAIN).setup(opts)` itself.
- Keep shared language/tool data in `lua/config/languages.lua` instead of
  duplicating lists across LSP, Mason, formatters, linters, Tree-sitter, or
  tests.
- Keep first-buffer filetype detection in `lua/config/filetypes.lua` for
  filetype-lazy plugins; do not depend only on plugin-owned `ftdetect` files.
- Gate plugins by upstream Neovim requirements. Core config must not fail on
  old Debian Neovim; LSP must support both Neovim 0.11+
  `vim.lsp.config` and the Neovim 0.10 `nvim-lspconfig` setup API.
- Keep Tree-sitter parser installation explicit. Do not enable parser
  auto-install at startup; tests should skip parser installation when
  `tree-sitter`, a C compiler, or `curl` is unavailable.
- Keep Mason opt-in through `NVIM_USE_MASON`. Default startup and background
  restore jobs must not install external tools.
- Keep blink.cmp on the stable v1 line and avoid binary/Rust requirements by
  default unless explicitly requested.
- Avoid duplicate plugin families for the same job, for example multiple
  indent-guide plugins.
- Validate Neovim changes with `go-task test:nvim` and preserve the lockfile
  diff check in that task. For startup-sensitive changes, also run
  `go-task test:nvim:profile`.
