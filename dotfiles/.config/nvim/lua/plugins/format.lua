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
      vim.g.strip_whitespace_on_save = 0
    end,
  },
  {
    "stevearc/conform.nvim",
    cmd = { "ConformInfo" },
    opts = {
      formatters_by_ft = languages.formatters_by_ft,
      default_format_opts = { timeout_ms = 3000, lsp_format = "never" },
      formatters = {
        biome = {
          require_cwd = true,
        },
      },
    },
  },
}
