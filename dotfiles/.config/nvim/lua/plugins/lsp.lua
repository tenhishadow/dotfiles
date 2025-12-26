if vim.fn.has("nvim-0.8") == 0 then
  return {}
end

return {
  --------------------------------------------------------------------
  -- Core LSP + Mason (servers wired in lua/lsp.lua)
  --------------------------------------------------------------------
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "WhoIsSethDaniel/mason-tool-installer.nvim",
      "b0o/schemastore.nvim",
    },
    config = function()
      -- mason: manage external LSP / formatters / linters
      local mason = require "mason"
      mason.setup()

      -- mason-lspconfig: install LSP servers
      local mason_lspconfig = require "mason-lspconfig"
      mason_lspconfig.setup({
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
        -- We use lua/lsp.lua to configure/enable servers, so let it
        -- handle vim.lsp.enable() instead of mason-lspconfig.
        automatic_enable = false,
      })

      -- mason-tool-installer: install non-LSP tools (formatters/linters)
      local mason_tool_installer = require "mason-tool-installer"
      mason_tool_installer.setup({
        ensure_installed = {
          -- Python
          "pyright",
          "ruff",
          "black",
          "isort",

          -- Terraform / HCL
          "terraform-ls",
          "tflint",

          -- YAML / Ansible
          "yaml-language-server",
          "yamllint",
          "ansible-language-server",
          "ansible-lint",

          -- Docker
          "dockerfile-language-server",
          "hadolint",

          -- Go
          "gopls",
          "actionlint",
          "awk-language-server",
          "azure-pipelines-language-server",
          "basics-language-server",
          "circleci-yaml-language-server",
          "commitlint",
          "copilot-language-server",
          "docker-compose-language-service",
          "docker-language-server",
          "dotenv-linter",
          "gitlab-ci-ls",
          "gitleaks",
          "google-java-format",
          "gradle-language-server",
          -- "groovy-language-server",
          "graphql-language-service-cli",
          "hclfmt",
          "helm-ls",
          "jq-lsp",
          "jsonlint",
          "jsonnet-language-server",
          "jsonnetfmt",
          "kube-linter",
          "lua-language-server",
          "postgres-language-server",
          "prometheus-pint",
          "semgrep",
          "shellcheck",
          "sqlfluff",
          "systemd-language-server",
          "systemdlint",
          "trivy"
        },
        auto_update = false,
        run_on_start = true,
      })
    end,
  },

  --------------------------------------------------------------------
  -- blink.cmp: completion engine (replaces nvim-cmp)
  --------------------------------------------------------------------
  {
    "saghen/blink.cmp",
    version = "1.*",
    event = "InsertEnter",
    dependencies = {
      -- Snippets (optional, but useful)
      "L3MON4D3/LuaSnip",
      "rafamadriz/friendly-snippets",
    },
    opts = {
      keymap = {
        -- Default preset: <Tab>/<S-Tab> navigate, <CR> confirm, etc.
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
      signature = {
        enabled = true,
      },
      sources = {
        -- Basic set: LSP + paths + buffer words
        default = { "lsp", "path", "buffer" },
      },
    },
    config = function(_, opts)
      local blink = require "blink.cmp"
      blink.setup(opts)

      -- Load VSCode-style snippets if LuaSnip is available
      local ok, luasnip = pcall(require, "luasnip")
      if ok then
        require("luasnip.loaders.from_vscode").lazy_load()
      end
    end,
  },
}
