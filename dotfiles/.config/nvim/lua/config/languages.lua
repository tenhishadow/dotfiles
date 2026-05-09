-- Shared language, tool and plugin data used by the Neovim config.

local M = {}

M.treesitter = {
  "lua",
  "vim",
  "vimdoc",
  "query",
  "python",
  "bash",
  "go",
  "yaml",
  "json",
  "dockerfile",
  "hcl",
  "terraform",
  "cue",
  "jsonnet",
  "rego",
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
  go = { "gofumpt", "goimports", "gofmt" },
  terraform = { "terraform_fmt" },
  ["terraform-vars"] = { "terraform_fmt" },
  opentofu = { "tofu_fmt" },
  ["opentofu-vars"] = { "tofu_fmt" },
  sh = { "shfmt" },
  bash = { "shfmt" },
  yaml = { "yamlfmt" },
  ["yaml.kubernetes"] = { "yamlfmt" },
  ["yaml.kustomize"] = { "yamlfmt" },
  ["yaml.docker-compose"] = { "yamlfmt" },
  ["yaml.gitlab"] = { "yamlfmt" },
  ["yaml.github-actions"] = { "yamlfmt" },
  ["yaml.helm-values"] = { "yamlfmt" },
  markdown = { "markdownlint-cli2" },

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
  cue = { "cue" },
  docker_compose_language_service = { "docker-compose-langserver" },
  dockerls = { "docker-langserver" },
  eslint = { "vscode-eslint-language-server", "eslint-language-server" },
  gh_actions_ls = { "gh-actions-language-server" },
  gitlab_ci_ls = { "gitlab-ci-ls" },
  gopls = { "gopls" },
  helm_ls = { "helm_ls", "helm-ls" },
  jsonnet_ls = { "jsonnet-language-server" },
  jsonls = {
    "vscode-json-language-server",
    "vscode-json-languageserver",
    "vscode-json-language-server-cli",
  },
  lua_ls = { "lua-language-server" },
  pylsp = { "pylsp" },
  pyright = { "pyright-langserver", "pyright" },
  regols = { "regols" },
  ruby_lsp = { "ruby-lsp" },
  systemd_lsp = { "systemd-language-server" },
  terraformls = { "terraform-ls" },
  tofu_ls = { "tofu-ls" },
  ts_ls = { "typescript-language-server" },
  yamlls = { "yaml-language-server" },
}

M.mason_lsp_servers = {
  "ansiblels",
  "bashls",
  "cue",
  "docker_compose_language_service",
  "dockerls",
  "gh_actions_ls",
  "gitlab_ci_ls",
  "gopls",
  "helm_ls",
  "jsonnet_ls",
  "jsonls",
  "lua_ls",
  "pyright",
  "regols",
  "ruby_lsp",
  "terraformls",
  "tofu_ls",
  "ts_ls",
  "yamlls",
}

-- Mason package names for general tools. LSP-only packages are installed
-- through mason_lsp_servers. External tools that are not in Mason's registry
-- stay in health/manual command inventories instead of this install list.
M.mason_tools = {
  "actionlint",
  "ansible-lint",
  "awk-language-server",
  "azure-pipelines-language-server",
  "basics-language-server",
  "black",
  "circleci-yaml-language-server",
  "commitlint",
  "copilot-language-server",
  "cue",
  "dotenv-linter",
  "gitleaks",
  "google-java-format",
  "gradle-language-server",
  "graphql-language-service-cli",
  "hadolint",
  "hclfmt",
  "isort",
  "jq-lsp",
  "jsonlint",
  "jsonnetfmt",
  "kube-linter",
  "markdownlint-cli2",
  "opa",
  "postgres-language-server",
  "prometheus-pint",
  "regal",
  "ruff",
  "semgrep",
  "shellcheck",
  "sqlfluff",
  "systemd-lsp",
  "systemdlint",
  "tflint",
  "trivy",
  "yamllint",
}

M.tool_bins = {
  ["ansible-language-server"] = { "ansible-language-server" },
  cue = { "cue" },
  ["docker-compose-language-service"] = { "docker-compose-langserver" },
  ["dockerfile-language-server"] = { "docker-langserver" },
  ["gh-actions-language-server"] = { "gh-actions-language-server" },
  ["gitlab-ci-ls"] = { "gitlab-ci-ls" },
  ["helm-ls"] = { "helm_ls", "helm-ls" },
  ["jsonnet-language-server"] = { "jsonnet-language-server" },
  kubeconform = { "kubeconform" },
  kustomize = { "kustomize" },
  ["lua-language-server"] = { "lua-language-server" },
  opa = { "opa" },
  pyright = { "pyright-langserver", "pyright" },
  regal = { "regal" },
  regols = { "regols" },
  ["ruby-lsp"] = { "ruby-lsp" },
  ["systemd-lsp"] = { "systemd-language-server" },
  ["terraform-ls"] = { "terraform-ls" },
  ["tofu-ls"] = { "tofu-ls" },
  ["yaml-language-server"] = { "yaml-language-server" },
}

M.yaml_schemas = {
  kubernetes = {
    "*.k8s.yaml",
    "*.k8s.yml",
    "k8s/**/*.yaml",
    "k8s/**/*.yml",
    "kubernetes/**/*.yaml",
    "kubernetes/**/*.yml",
    "manifests/**/*.yaml",
    "manifests/**/*.yml",
    "deploy/**/*.yaml",
    "deploy/**/*.yml",
    "deployments/**/*.yaml",
    "deployments/**/*.yml",
    "clusters/**/*.yaml",
    "clusters/**/*.yml",
    "apps/**/*.yaml",
    "apps/**/*.yml",
    "base/**/*.yaml",
    "base/**/*.yml",
    "overlays/**/*.yaml",
    "overlays/**/*.yml",
  },
  ["https://json.schemastore.org/chart.json"] = {
    "**/Chart.yaml",
    "**/Chart.yml",
  },
  ["https://json.schemastore.org/kustomization.json"] = {
    "**/kustomization.yaml",
    "**/kustomization.yml",
    "**/Kustomization",
  },
}

M.health_tools = {
  {
    section = "Core tools",
    tools = {
      { label = "git", commands = { "git" }, required = true },
      { label = "curl", commands = { "curl" } },
      { label = "ripgrep", commands = { "rg" } },
      { label = "make", commands = { "make" } },
      { label = "unzip", commands = { "unzip" } },
    },
  },
  {
    section = "Platform tools",
    tools = {
      { label = "kubectl", commands = { "kubectl" } },
      { label = "helm", commands = { "helm" } },
      { label = "kustomize", commands = { "kustomize" } },
      { label = "terraform", commands = { "terraform" } },
      { label = "OpenTofu", commands = { "tofu" } },
    },
  },
  {
    section = "Validation and security tools",
    tools = {
      { label = "ansible-lint", commands = { "ansible-lint" } },
      { label = "shellcheck", commands = { "shellcheck" } },
      { label = "gitleaks", commands = { "gitleaks" } },
      { label = "trivy", commands = { "trivy" } },
      { label = "kubeconform", commands = { "kubeconform" } },
      { label = "semgrep", commands = { "semgrep" } },
    },
  },
}

-- Fast, file-local linters that are safe to run automatically after save.
M.auto_linters_by_ft = {
  bash = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
  dockerfile = {
    { name = "hadolint", cmd = "hadolint" },
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
  yaml = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.kubernetes"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.kustomize"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.docker-compose"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.gitlab"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.github-actions"] = {
    { name = "actionlint", cmd = "actionlint" },
  },
  ["yaml.helm-values"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  ["yaml.ansible"] = {
    { name = "yamllint", cmd = "yamllint" },
  },
  zsh = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
}

-- Project-wide or security/policy linters stay manual to avoid slow, noisy, or
-- unsafe automatic process execution while navigating infrastructure repos.
M.manual_linters_by_ft = {
  ansible = {
    { name = "ansible_lint", cmd = "ansible-lint" },
  },
  cue = {
    { name = "cue", cmd = "cue" },
  },
  hcl = {
    { name = "tflint", cmd = "tflint" },
  },
  opentofu = {
    { name = "tofu", cmd = "tofu" },
  },
  ["opentofu-vars"] = {
    { name = "tofu", cmd = "tofu" },
  },
  rego = {
    { name = "regal", cmd = "regal" },
    { name = "opa_check", cmd = "opa" },
  },
  sql = {
    { name = "sqlfluff", cmd = "sqlfluff" },
  },
  terraform = {
    { name = "tflint", cmd = "tflint" },
  },
  ["terraform-vars"] = {
    { name = "tflint", cmd = "tflint" },
  },
  ["yaml.ansible"] = {
    { name = "ansible_lint", cmd = "ansible-lint" },
  },
}

M.linters_by_ft = M.auto_linters_by_ft

return M
