return {
  -- Respect project-level formatting settings
  { "editorconfig/editorconfig-vim" },

  -- Text alignment
  {
    "junegunn/vim-easy-align",
    keys = {
      { "ga", "<Plug>(EasyAlign)", mode = { "n", "x" } },
    },
  },

  -- Indent guides
  {
    "nathanaelkane/vim-indent-guides",
    event = "BufReadPre",
  },

  -- Highlight trailing whitespace
  {
    "ntpeters/vim-better-whitespace",
    event = "BufReadPre",
    init = function()
      vim.g.better_whitespace_enabled = 1
    end,
  },

  -- On-save formatting powered by external tools
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    opts = {
      formatters_by_ft = {
        python = { "ruff_format", "black" },
        lua = { "stylua" },
        terraform = { "terraform_fmt" },
        sh = { "shfmt" },
        bash = { "shfmt" },
        yaml = { "yamlfmt" },
        markdown = { "markdownlint" },
      },
      format_on_save = function(bufnr)
        if vim.g.disable_autoformat or vim.b[bufnr].disable_autoformat then
          return
        end
        return { timeout_ms = 3000, lsp_fallback = true }
      end,
    },
  },
}
