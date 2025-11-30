-- lua/lsp.lua
local M = {}

----------------------------------------------------------------------
-- Helper to configure LSP servers for both the new API (0.11+) and classic lspconfig
----------------------------------------------------------------------
local function lsp_setup(server, opts)
  opts = opts or {}
  if vim.lsp and vim.lsp.enable and vim.lsp.config then
    -- Neovim 0.11+ style
    vim.lsp.config(server, opts)
    vim.lsp.enable(server)
  else
    -- Classic nvim-lspconfig style
    require("lspconfig")[server].setup(opts)
  end
end

----------------------------------------------------------------------
-- nvim-cmp (optional / lazy-safe setup)
----------------------------------------------------------------------
local has_cmp, cmp = pcall(require, "cmp")
if has_cmp then
  local ok_snip, luasnip = pcall(require, "luasnip")
  cmp.setup({
    snippet = {
      expand = function(args)
        if ok_snip then
          luasnip.lsp_expand(args.body)
        end
      end,
    },
    mapping = cmp.mapping.preset.insert({
      ["<C-Space>"] = cmp.mapping.complete(),
      ["<CR>"] = cmp.mapping.confirm({ select = true }),
    }),
    sources = cmp.config.sources({
      { name = "nvim_lsp" },
      ok_snip and { name = "luasnip" } or nil,
      { name = "path" },
    }),
  })
end

----------------------------------------------------------------------
-- CAPABILITIES (extended with cmp support when available)
----------------------------------------------------------------------
local capabilities = vim.lsp.protocol.make_client_capabilities()
do
  local ok_cmpcaps, cmp_lsp = pcall(require, "cmp_nvim_lsp")
  if ok_cmpcaps then
    capabilities = cmp_lsp.default_capabilities(capabilities)
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
          [sev.WARN] = icons.Warn,
          [sev.HINT] = icons.Hint,
          [sev.INFO] = icons.Info,
        },
        -- numhl/texthl can be added here if you want
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
-- on_attach: keymaps + inlay hints (handles both old and new APIs)
----------------------------------------------------------------------
local function on_attach(_, bufnr)
  local function map(mode, lhs, rhs, desc)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true, desc = desc })
  end

  map("n", "gd", vim.lsp.buf.definition, "LSP: Go to Definition")
  map("n", "K", vim.lsp.buf.hover, "LSP: Hover")
  map("n", "gi", vim.lsp.buf.implementation, "LSP: Go to Implementation")
  map("n", "<leader>rn", vim.lsp.buf.rename, "LSP: Rename")
  map("n", "<leader>ca", vim.lsp.buf.code_action, "LSP: Code Action")
  map("n", "[d", vim.diagnostic.goto_prev, "LSP: Prev Diagnostic")
  map("n", "]d", vim.diagnostic.goto_next, "LSP: Next Diagnostic")
  map("n", "<leader>q", vim.diagnostic.setloclist, "LSP: Diagnostics to LocList")

  -- Inlay hints: Neovim 0.10 (function) vs 0.11+ (table + enable)
  local ih = vim.lsp.inlay_hint
  if type(ih) == "table" and ih.enable then
    pcall(ih.enable, true, { bufnr = bufnr })
  elseif type(ih) == "function" then
    pcall(ih, bufnr, true)
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
-- Server-specific configs, gated by actual binaries in the system
----------------------------------------------------------------------
local server_configs = {}

local function add_server(name, cfg)
  server_configs[name] = cfg or {}
end

----------------------------------------------------------------------
-- Python: prefer pyright for speed & type-checking; fall back to pylsp
----------------------------------------------------------------------
if has_any({ "pyright-langserver", "pyright" }) then
  add_server("pyright", {})
elseif has_any("pylsp") then
  add_server("pylsp", {
    settings = {
      pylsp = {
        plugins = {
          black = { enabled = true },
          pycodestyle = { enabled = false },
          mccabe = { enabled = false },
          pyflakes = { enabled = false },
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
-- YAML
----------------------------------------------------------------------
if has_any("yaml-language-server") then
  add_server("yamlls")
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
-- JSON
----------------------------------------------------------------------
if has_any({ "vscode-json-language-server", "vscode-json-languageserver", "vscode-json-language-server-cli" }) then
  add_server("jsonls")
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
  add_server("tsserver", {
    cmd = { "typescript-language-server", "--stdio" },
  })
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
  add_server("systemd")
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
