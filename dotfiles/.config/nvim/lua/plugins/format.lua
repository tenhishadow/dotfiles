return {
  -- Respect project-level formatting settings
  { "editorconfig/editorconfig-vim" },

  -- Text alignment
  {
    "junegunn/vim-easy-align",
    keys = {
      -- remap = true is required so that <Plug>(EasyAlign) expands properly
      { "ga", "<Plug>(EasyAlign)", mode = { "n", "x" }, remap = true },
    },
  },

  -- Indent guides
  {
    "nathanaelkane/vim-indent-guides",
    event = "BufReadPre",
    init = function()
      vim.g.indent_guides_enable_on_vim_startup = 1
      vim.g.indent_guides_auto_colors = 0
    end,
  },

  -- Highlight trailing whitespace
  {
    "ntpeters/vim-better-whitespace",
    event = "BufReadPre",
    init = function()
      vim.g.better_whitespace_enabled = 1
    end,
  },

  -- Conform: unified formatter integration
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    opts = {
      formatters_by_ft = {
        python    = { "ruff_format", "black" },
        lua       = { "stylua" },
        terraform = { "terraform_fmt" },
        sh        = { "shfmt" },
        bash      = { "shfmt" },
        yaml      = { "yamlfmt" },
        markdown  = { "markdownlint" },

        -- Web / JSON via Biome (if installed)
        json             = { "biome" },
        jsonc            = { "biome" },
        javascript       = { "biome" },
        javascriptreact  = { "biome" },
        typescript       = { "biome" },
        typescriptreact  = { "biome" },
        css              = { "biome" },
      },

      -- Format on save unless explicitly disabled.
      format_on_save = function(bufnr)
        if vim.g.disable_autoformat or vim.b[bufnr].disable_autoformat then
          return
        end
        return { timeout_ms = 3000, lsp_format = "never" }
      end,

      -- Extra per-formatter settings
      formatters = {
        biome = {
          -- Only run Biome when there is a project root (biome.json / biome.jsonc),
          -- so random JSON files outside projects are not affected.
          require_cwd = true,
        },
      },
    },
  },
}
