if vim.fn.has("nvim-0.8") == 0 then
  return {}
end

return {
  -- Core LSP client configuration (servers are wired in lua/lsp.lua)
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      "b0o/schemastore.nvim"
    },
    config = function()
      -- mason: manage external LSP / formatters / linters
      require("mason").setup()

      -- Ensure core language servers are installed; setup happens in lua/lsp.lua
      require("mason-lspconfig").setup({
        ensure_installed = {
          "bashls",
          "pyright",
          "terraformls",
          "solargraph",
          "yamlls",
          "dockerls",
          "ansiblels",
          "jsonls",
          "gopls",
        },
        automatic_installation = true,
        automatic_enable = false
      })

      -- Dev tools: formatters / linters for Python + DevOps
      require("mason-tool-installer").setup({
        ensure_installed = {
          -- Python
          "pyright",
          "ruff",
          "black",
          "isort",

          -- Terraform
          "terraformls",
          "tflint",

          -- YAML / Ansible
          "yamlls",
          "yamllint",
          "ansible-language-server",
          "ansible-lint",

          -- Docker
          "dockerls",
          "hadolint",

          -- Go (for tooling)
          "gopls",
        },
        auto_update = false,
        run_on_start = true,
      })
    end,
  },

  -- Completion engine
  {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-path",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp = require("cmp")
      local luasnip = require("luasnip")

      cmp.setup({
        snippet = {
          expand = function(args)
            luasnip.lsp_expand(args.body)
          end,
        },
        mapping = cmp.mapping.preset.insert({
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
          ["<C-Space>"] = cmp.mapping.complete(),
        }),
        sources = {
          { name = "nvim_lsp" },
          { name = "path" },
          { name = "luasnip" },
        },
      })
    end,
  },

  -- Expose cmp capabilities to LSP
  { "hrsh7th/cmp-nvim-lsp" },

  -- Path completion
  { "hrsh7th/cmp-path" },

  -- Snippets
  { "L3MON4D3/LuaSnip" },
  { "saadparwaiz1/cmp_luasnip" },
}
