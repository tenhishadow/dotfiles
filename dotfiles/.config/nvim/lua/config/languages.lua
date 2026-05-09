-- Shared language, tool and plugin data used by the Neovim config.

local M = {}

M.treesitter = {
  "lua",
  "vim",
  "vimdoc",
  "query",
  "python",
  "bash",
  "yaml",
  "json",
  "markdown",
  "markdown_inline",
}

M.treesitter_install_requirements = {
  {
    label = "tree-sitter CLI",
    commands = { "tree-sitter" },
  },
  {
    label = "C compiler",
    commands = { "cc", "gcc", "clang" },
  },
  {
    label = "curl",
    commands = { "curl" },
  },
}

M.formatters_by_ft = {
  python = { "ruff_format", "black" },
  lua = { "stylua" },
  terraform = { "terraform_fmt" },
  sh = { "shfmt" },
  bash = { "shfmt" },
  yaml = { "yamlfmt" },
  markdown = { "markdownlint" },

  json = { "biome" },
  jsonc = { "biome" },
  javascript = { "biome" },
  javascriptreact = { "biome" },
  typescript = { "biome" },
  typescriptreact = { "biome" },
  css = { "biome" },
}

M.lsp_bins = {
  ansiblels = { "ansible-language-server" },
  bashls = { "bash-language-server" },
  dockerls = { "docker-langserver" },
  eslint = { "vscode-eslint-language-server", "eslint-language-server" },
  gopls = { "gopls" },
  helm_ls = { "helm_ls", "helm-ls" },
  jsonls = {
    "vscode-json-language-server",
    "vscode-json-languageserver",
    "vscode-json-language-server-cli",
  },
  lua_ls = { "lua-language-server" },
  pylsp = { "pylsp" },
  pyright = { "pyright-langserver", "pyright" },
  ruby_lsp = { "ruby-lsp" },
  systemd_lsp = { "systemd-language-server" },
  terraformls = { "terraform-ls" },
  ts_ls = { "typescript-language-server" },
  yamlls = { "yaml-language-server" },
}

M.mason_lsp_servers = {
  "ansiblels",
  "bashls",
  "dockerls",
  "gopls",
  "jsonls",
  "lua_ls",
  "pyright",
  "ruby_lsp",
  "terraformls",
  "ts_ls",
  "yamlls",
}

M.mason_tools = {
  "actionlint",
  "ansible-language-server",
  "ansible-lint",
  "awk-language-server",
  "azure-pipelines-language-server",
  "bash-language-server",
  "basics-language-server",
  "black",
  "circleci-yaml-language-server",
  "commitlint",
  "copilot-language-server",
  "docker-compose-language-service",
  "docker-language-server",
  "dockerfile-language-server",
  "dotenv-linter",
  "gitlab-ci-ls",
  "gitleaks",
  "google-java-format",
  "gopls",
  "gradle-language-server",
  "graphql-language-service-cli",
  "hadolint",
  "hclfmt",
  "helm-ls",
  "isort",
  "jq-lsp",
  "jsonlint",
  "jsonnet-language-server",
  "jsonnetfmt",
  "kube-linter",
  "lua-language-server",
  "postgres-language-server",
  "prometheus-pint",
  "pyright",
  "ruby-lsp",
  "ruff",
  "semgrep",
  "shellcheck",
  "sqlfluff",
  "systemd-language-server",
  "systemdlint",
  "terraform-ls",
  "tflint",
  "trivy",
  "yaml-language-server",
  "yamllint",
}

M.tool_bins = {
  ["ansible-language-server"] = { "ansible-language-server" },
  ["dockerfile-language-server"] = { "docker-langserver" },
  ["helm-ls"] = { "helm_ls", "helm-ls" },
  ["lua-language-server"] = { "lua-language-server" },
  pyright = { "pyright-langserver", "pyright" },
  ["ruby-lsp"] = { "ruby-lsp" },
  ["systemd-language-server"] = { "systemd-language-server" },
  ["terraform-ls"] = { "terraform-ls" },
  ["yaml-language-server"] = { "yaml-language-server" },
}

M.linters_by_ft = {
  ansible = {
    { name = "ansible_lint", cmd = "ansible-lint" },
  },
  bash = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
  dockerfile = {
    { name = "hadolint", cmd = "hadolint" },
  },
  hcl = {
    { name = "tflint", cmd = "tflint" },
  },
  json = {
    { name = "jsonlint", cmd = "jsonlint" },
  },
  lua = {
    { name = "luacheck", cmd = "luacheck" },
  },
  markdown = {
    { name = "markdownlint", cmd = "markdownlint-cli2" },
  },
  python = {
    { name = "ruff", cmd = "ruff" },
  },
  sh = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
  sql = {
    { name = "sqlfluff", cmd = "sqlfluff" },
  },
  terraform = {
    { name = "tflint", cmd = "tflint" },
  },
  yaml = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.ansible"] = {
    { name = "yamllint", cmd = "yamllint" },
    { name = "ansible_lint", cmd = "ansible-lint" },
  },
  zsh = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
}

return M
