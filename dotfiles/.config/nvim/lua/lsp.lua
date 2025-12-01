-- lua/lsp.lua
local M = {}

----------------------------------------------------------------------
-- Optional: require nvim-lspconfig (used for older Neovim API)
----------------------------------------------------------------------
local has_lspconfig, lspconfig = pcall(require, "lspconfig")

----------------------------------------------------------------------
-- Helper to configure LSP servers for both the new API (0.11+)
-- and the classic nvim-lspconfig API.
----------------------------------------------------------------------
local function lsp_setup(server, opts)
  opts = opts or {}

  -- Neovim 0.11+ style (vim.lsp.config / vim.lsp.enable)
  if vim.lsp and vim.lsp.enable and vim.lsp.config then
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

----------------------

