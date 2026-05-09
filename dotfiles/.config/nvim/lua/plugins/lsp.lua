if vim.fn.has("nvim-0.11.3") == 0 then
  return {}
end

local languages = require("config.languages")
local mason_utils = require("utils.mason")
local mason_mode = mason_utils.resolve_mode()

return {
  {
    "mason-org/mason.nvim",
    enabled = mason_mode ~= "off",
    opts = {
      PATH = mason_mode == "auto" and "append" or "prepend",
    },
  },
  {
    "mason-org/mason-lspconfig.nvim",
    enabled = mason_mode ~= "off",
    dependencies = {
      "mason-org/mason.nvim",
      "neovim/nvim-lspconfig",
    },
    opts = function()
      local ensure_installed = {}
      if mason_mode == "always" then
        ensure_installed = languages.mason_lsp_servers
      end
      return {
        ensure_installed = ensure_installed,
        automatic_enable = false,
      }
    end,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    enabled = mason_mode ~= "off",
    dependencies = { "mason-org/mason.nvim" },
    opts = function()
      local ensure_installed = languages.mason_tools
      if mason_mode == "auto" then
        ensure_installed = mason_utils.filter_missing(ensure_installed, languages.tool_bins)
      end
      return {
        ensure_installed = ensure_installed,
        auto_update = false,
        run_on_start = mason_mode == "always",
      }
    end,
  },
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "b0o/schemastore.nvim",
    },
    config = function()
      require("config.lsp").setup()
    end,
  },
}
