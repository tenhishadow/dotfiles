if vim.fn.has("nvim-0.10") == 0 then
  return {}
end

return {
  {
    "saghen/blink.cmp",
    version = "1.*",
    event = "InsertEnter",
    dependencies = {
      "L3MON4D3/LuaSnip",
      "rafamadriz/friendly-snippets",
    },
    opts = {
      keymap = {
        preset = "default",
      },
      completion = {
        documentation = {
          auto_show = true,
          auto_show_delay_ms = 200,
        },
        menu = {
          border = "rounded",
        },
      },
      fuzzy = {
        implementation = vim.env.NVIM_BLINK_FUZZY or "lua",
      },
      signature = {
        enabled = true,
      },
      sources = {
        default = { "lsp", "path", "buffer" },
      },
    },
    config = function(_, opts)
      require("blink.cmp").setup(opts)
      pcall(function()
        require("luasnip.loaders.from_vscode").lazy_load()
      end)
    end,
  },
}
