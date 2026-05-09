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
  "cue",
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
  "kubeconform",
  "kustomize",
  "isort",
  "jq-lsp",
  "jsonlint",
  "jsonnet-language-server",
  "jsonnetfmt",
  "kube-linter",
  "lua-language-server",
  "opa",
  "postgres-language-server",
  "prometheus-pint",
  "pyright",
  "regal",
  "regols",
  "ruby-lsp",
  "ruff",
  "semgrep",
  "shellcheck",
  "sqlfluff",
  "systemd-language-server",
  "systemdlint",
  "terraform-ls",
  "tflint",
  "tofu-ls",
  "trivy",
  "yaml-language-server",
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
  ["systemd-language-server"] = { "systemd-language-server" },
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
  cue = {
    { name = "cue", cmd = "cue" },
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
  rego = {
    { name = "regal", cmd = "regal" },
    { name = "opa_check", cmd = "opa" },
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
  ["terraform-vars"] = {
    { name = "tflint", cmd = "tflint" },
  },
  opentofu = {
    { name = "tofu", cmd = "tofu" },
  },
  ["opentofu-vars"] = {
    { name = "tofu", cmd = "tofu" },
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
    { name = "ansible_lint", cmd = "ansible-lint" },
  },
  zsh = {
    { name = "shellcheck", cmd = "shellcheck" },
  },
}

return M
