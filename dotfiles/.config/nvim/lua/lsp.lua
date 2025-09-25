-- lua/lsp.lua
local M = {}

----------------------------------------------------------------------
-- Нормализатор запуска LSP: новый API (0.11+) и старый (lspconfig)
----------------------------------------------------------------------
local function lsp_setup(server, opts)
  opts = opts or {}
  if vim.lsp and vim.lsp.enable and vim.lsp.config then
    vim.lsp.config(server, opts)
    vim.lsp.enable(server)
  else
    require("lspconfig")[server].setup(opts)
  end
end

----------------------------------------------------------------------
-- nvim-cmp (мягкое подключение)
----------------------------------------------------------------------
local has_cmp, cmp = pcall(require, "cmp")
if has_cmp then
  local ok_snip, luasnip = pcall(require, "luasnip")
  cmp.setup({
    snippet = {
      expand = function(args)
        if ok_snip then luasnip.lsp_expand(args.body) end
      end,
    },
    mapping = cmp.mapping.preset.insert({
      ["<C-Space>"] = cmp.mapping.complete(),
      ["<CR>"]      = cmp.mapping.confirm({ select = true }),
    }),
    sources = cmp.config.sources({
      { name = "nvim_lsp" },
      ok_snip and { name = "luasnip" } or nil,
      { name = "path" },
    }),
  })
end

----------------------------------------------------------------------
-- CAPABILITIES (с поддержкой cmp, если есть)
----------------------------------------------------------------------
local capabilities = vim.lsp.protocol.make_client_capabilities()
do
  local ok_cmpcaps, cmp_lsp = pcall(require, "cmp_nvim_lsp")
  if ok_cmpcaps then capabilities = cmp_lsp.default_capabilities(capabilities) end
end

----------------------------------------------------------------------
-- Диагностики и знаки (без deprecated sign_define на новых версиях)
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
        -- numhl/texthl можно добавить при желании
      },
      underline = true,
      update_in_insert = false,
      severity_sort = true,
      float = { border = "rounded", source = "always" },
    })
  else
    -- Старый Neovim: аккуратный фоллбэк
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
-- on_attach: keymaps + inlay hints (учёт разных API)
----------------------------------------------------------------------
local function on_attach(_, bufnr)
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

  -- Inlay hints: 0.10 (fn), 0.11+ (table+enable)
  local ih = vim.lsp.inlay_hint
  if type(ih) == "table" and ih.enable then
    pcall(ih.enable, true, { bufnr = bufnr })
  elseif type(ih) == "function" then
    pcall(ih, bufnr, true)
  end
end

----------------------------------------------------------------------
-- Серверы и общие опции
----------------------------------------------------------------------
local servers = {
  "bashls", "pyright", "terraformls", "solargraph", "yamlls",
  "dockerls", "ansiblels", "jsonls", "gopls",
}

local base_opts = {
  capabilities = capabilities,
  on_attach = on_attach,
}

for _, s in ipairs(servers) do
  lsp_setup(s, base_opts)
end

return M

