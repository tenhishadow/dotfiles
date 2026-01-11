-- lua/lsp.lua
-- LSP server configuration, diagnostics and keymaps.

local M = {}

----------------------------------------------------------------------
-- Detect whether the new Neovim 0.11+ LSP API is available
----------------------------------------------------------------------
local has_new_lsp = vim.lsp and vim.lsp.config and vim.lsp.enable

----------------------------------------------------------------------
-- Optional: require nvim-lspconfig only on older Neovim
-- (to avoid the deprecated framework warning on 0.11+)
----------------------------------------------------------------------
local has_lspconfig, lspconfig = false, nil
if not has_new_lsp then
  has_lspconfig, lspconfig = pcall(require, "lspconfig")
end

----------------------------------------------------------------------
-- Helper to configure LSP servers for both the new API (0.11+)
-- and the classic nvim-lspconfig API.
----------------------------------------------------------------------
local function lsp_setup(server, opts)
  opts = opts or {}

  -- Neovim 0.11+ style (vim.lsp.config / vim.lsp.enable)
  if has_new_lsp then
    vim.lsp.config(server, opts)
    vim.lsp.enable(server)
    return
  end

  -- Legacy style via nvim-lspconfig
  if has_lspconfig and lspconfig[server] then
    lspconfig[server].setup(opts)
  end
end

----------------------------------------------------------------------
-- CAPABILITIES (extended with completion engine support)
----------------------------------------------------------------------
local capabilities = vim.lsp.protocol.make_client_capabilities()
do
  -- Prefer blink.cmp if installed
  local ok_blink, blink = pcall(require, "blink.cmp")
  if ok_blink and blink.get_lsp_capabilities then
    capabilities = blink.get_lsp_capabilities(capabilities)
  else
    -- Fallback to cmp_nvim_lsp if blink.cmp is not available
    local ok_cmpcaps, cmp_lsp = pcall(require, "cmp_nvim_lsp")
    if ok_cmpcaps then
      capabilities = cmp_lsp.default_capabilities(capabilities)
    end
  end
end

----------------------------------------------------------------------
-- Diagnostics and signs (avoid deprecated sign_define on newer versions)
----------------------------------------------------------------------
local icons = { Error = "", Warn = "", Hint = "", Info = "" }

local function setup_diagnostic_signs()
  if vim.diagnostic and vim.diagnostic.config then
    local sev = vim.diagnostic.severity
    vim.diagnostic.config({
      virtual_text = false,
      signs = {
        text = {
          [sev.ERROR] = icons.Error,
          [sev.WARN]  = icons.Warn,
          [sev.HINT]  = icons.Hint,
          [sev.INFO]  = icons.Info,
        },
      },
      underline = true,
      update_in_insert = false,
      severity_sort = true,
      float = { border = "rounded", source = "always" },
    })
  else
    -- Legacy Neovim: fall back to classic sign_define
    for kind, icon in pairs(icons) do
      local hl = "DiagnosticSign" .. kind
      if vim.fn.hlexists(hl) == 0 and vim.fn.hlexists("LspDiagnosticsSign" .. kind) == 1 then
        hl = "LspDiagnosticsSign" .. kind
      end
      vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = "" })
    end
  end
end
setup_diagnostic_signs()

----------------------------------------------------------------------
-- Helper: decide if we want inlay hints for given client + buffer
----------------------------------------------------------------------
local function supports_inlay_hints(client, bufnr)
  if not (client.server_capabilities and client.server_capabilities.inlayHintProvider) then
    return false
  end

  local ft = vim.bo[bufnr].filetype

  -- Allowlist of filetypes per server where inlay hints actually make sense.
  local allowed = {
    pyright  = { "python" },
    pylsp    = { "python" },
    lua_ls   = { "lua" },
    tsserver = { "typescript", "typescriptreact", "javascript", "javascriptreact" },
    ts_ls    = { "typescript", "typescriptreact", "javascript", "javascriptreact" },
    gopls    = { "go" },
  }

  local fts = allowed[client.name]
  if not fts then
    return false
  end

  for _, v in ipairs(fts) do
    if v == ft then
      return true
    end
  end

  return false
end

----------------------------------------------------------------------
-- on_attach: keymaps + inlay hints (safe per-client / per-filetype)
----------------------------------------------------------------------
local function on_attach(client, bufnr)
  local function map(mode, lhs, rhs, desc)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true, desc = desc })
  end

  map("n", "gd", vim.lsp.buf.definition,           "LSP: Go to Definition")
  map("n", "K",  vim.lsp.buf.hover,                "LSP: Hover")
  map("n", "gi", vim.lsp.buf.implementation,       "LSP: Go to Implementation")
  map("n", "<leader>rn", vim.lsp.buf.rename,       "LSP: Rename")
  map("n", "<leader>ca", vim.lsp.buf.code_action,  "LSP: Code Action")
  map("n", "[d", vim.diagnostic.goto_prev,         "LSP: Prev Diagnostic")
  map("n", "]d", vim.diagnostic.goto_next,         "LSP: Next Diagnostic")
  map("n", "<leader>q", vim.diagnostic.setloclist, "LSP: Diagnostics to LocList")

  -- Only enable inlay hints where the server + filetype are whitelisted
  if supports_inlay_hints(client, bufnr) then
    local ih = vim.lsp.inlay_hint
    if type(ih) == "table" and ih.enable then
      pcall(ih.enable, true, { bufnr = bufnr })
    elseif type(ih) == "function" then
      pcall(ih, bufnr, true)
    end
  end
end

----------------------------------------------------------------------
-- Helper: check whether any of the given binaries exist in $PATH
----------------------------------------------------------------------
local function has_any(cmds)
  if type(cmds) == "string" then
    cmds = { cmds }
  end
  for _, cmd in ipairs(cmds) do
    if vim.fn.executable(cmd) == 1 then
      return true
    end
  end
  return false
end

----------------------------------------------------------------------
-- Resolve server names that changed in recent nvim-lspconfig versions
-- On Neovim 0.11+ we do not require('lspconfig'), so we just prefer the
-- modern "ts_ls" name. On older setups we fall back to detection via
-- lspconfig if available.
----------------------------------------------------------------------
local TS_SERVER
if has_new_lsp then
  TS_SERVER = "ts_ls"
elseif has_lspconfig and lspconfig and lspconfig.ts_ls then
  TS_SERVER = "ts_ls"
else
  TS_SERVER = "tsserver"
end

local SYSTEMD_SERVER = "systemd_lsp"  -- modern name in nvim-lspconfig

----------------------------------------------------------------------
-- SchemaStore (optional, for JSON/YAML schemas)
----------------------------------------------------------------------
local ok_schemastore, schemastore = pcall(require, "schemastore")

----------------------------------------------------------------------
-- Server-specific configs, gated by actual binaries in the system
----------------------------------------------------------------------
local server_configs = {}

local function add_server(name, cfg)
  server_configs[name] = cfg or {}
end

----------------------------------------------------------------------
-- Python: prefer pyright; fall back to pylsp with black plugin
----------------------------------------------------------------------
if has_any({ "pyright-langserver", "pyright" }) then
  add_server("pyright", {})
elseif has_any("pylsp") then
  add_server("pylsp", {
    settings = {
      pylsp = {
        plugins = {
          black       = { enabled = true },
          pycodestyle = { enabled = false },
          mccabe      = { enabled = false },
          pyflakes    = { enabled = false },
        },
      },
    },
  })
end

----------------------------------------------------------------------
-- Bash
----------------------------------------------------------------------
if has_any("bash-language-server") then
  add_server("bashls")
end

----------------------------------------------------------------------
-- YAML (with SchemaStore if available)
----------------------------------------------------------------------
if has_any("yaml-language-server") then
  local yaml_settings = {
    redhat = { telemetry = { enabled = false } },
    yaml = {
      keyOrdering = false,
      format = { enable = true },
      validate = true,
      schemaStore = {
        enable = false, -- we use schemastore.nvim instead
        url = "",
      },
    },
  }

  if ok_schemastore then
    yaml_settings.yaml.schemas = schemastore.yaml.schemas()
  end

  add_server("yamlls", {
    settings = yaml_settings,
  })
end

----------------------------------------------------------------------
-- Terraform / HCL
----------------------------------------------------------------------
if has_any("terraform-ls") then
  add_server("terraformls")
end

----------------------------------------------------------------------
-- Docker
----------------------------------------------------------------------
if has_any("docker-langserver") then
  add_server("dockerls")
end

----------------------------------------------------------------------
-- Ansible
----------------------------------------------------------------------
if has_any("ansible-language-server") then
  add_server("ansiblels")
end

----------------------------------------------------------------------
-- JSON (with SchemaStore if available)
----------------------------------------------------------------------
if has_any({ "vscode-json-language-server", "vscode-json-languageserver", "vscode-json-language-server-cli" }) then
  local json_settings = {
    json = {
      format = { enable = true },
      validate = { enable = true },
    },
  }

  if ok_schemastore then
    json_settings.json.schemas = schemastore.json.schemas()
  end

  add_server("jsonls", {
    settings = json_settings,
  })
end

----------------------------------------------------------------------
-- Go
----------------------------------------------------------------------
if has_any("gopls") then
  add_server("gopls")
end

----------------------------------------------------------------------
-- Lua (for Neovim config)
----------------------------------------------------------------------
if has_any("lua-language-server") then
  add_server("lua_ls", {
    settings = {
      Lua = {
        diagnostics = {
          globals = { "vim" },
        },
        workspace = {
          checkThirdParty = false,
          -- Restrict workspace to Neovim runtime + config instead of $HOME
          library = {
            vim.env.VIMRUNTIME,
            vim.fn.stdpath("config"),
          },
        },
        telemetry = { enable = false },
      },
    },
  })
end

----------------------------------------------------------------------
-- TypeScript / JavaScript
----------------------------------------------------------------------
if has_any("typescript-language-server") then
  add_server(TS_SERVER, {
    cmd = { "typescript-language-server", "--stdio" },
  })
end

----------------------------------------------------------------------
-- Helm (Helm charts)
----------------------------------------------------------------------
if has_any({ "helm_ls", "helm-ls" }) then
  add_server("helm_ls")
end

----------------------------------------------------------------------
-- ESLint (for JS/TS projects)
----------------------------------------------------------------------
if has_any({ "vscode-eslint-language-server", "eslint-language-server" }) then
  add_server("eslint")
end

----------------------------------------------------------------------
-- Systemd unit files
----------------------------------------------------------------------
if has_any("systemd-language-server") then
  add_server(SYSTEMD_SERVER)
end

----------------------------------------------------------------------
-- Ruby (ruby-lsp)
----------------------------------------------------------------------
if has_any("ruby-lsp") then
  add_server("ruby_lsp")
end

----------------------------------------------------------------------
-- Apply base options and configure all detected servers
----------------------------------------------------------------------
local base_opts = {
  capabilities = capabilities,
  on_attach = on_attach,
}

for server, cfg in pairs(server_configs) do
  local opts = vim.tbl_deep_extend("force", base_opts, cfg or {})
  lsp_setup(server, opts)
end

return M
