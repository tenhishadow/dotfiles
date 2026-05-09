local languages = require("config.languages")
local keymaps = require("config.keymaps_spec")

return {
  {
    "editorconfig/editorconfig-vim",
    enabled = vim.fn.has("nvim-0.9") == 0,
  },
  {
    "junegunn/vim-easy-align",
    keys = keymaps.to_lazy_keys(keymaps.editing),
  },
  {
    "ntpeters/vim-better-whitespace",
    event = "BufReadPre",
    init = function()
      vim.g.better_whitespace_enabled = 1
    end,
  },
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    opts = {
      formatters_by_ft = languages.formatters_by_ft,
      format_on_save = function(bufnr)
        if vim.g.disable_autoformat or vim.b[bufnr].disable_autoformat then
          return
        end
        return { timeout_ms = 3000, lsp_format = "never" }
      end,
      formatters = {
        biome = {
          require_cwd = true,
        },
      },
    },
  },
}
