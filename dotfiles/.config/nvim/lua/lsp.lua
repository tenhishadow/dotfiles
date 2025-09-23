-- lua/lsp.lua
local M = {}

----------------------------------------------------------------------
-- Совместимость нового/старого API
-- new (0.11+): vim.lsp.config(<name>, <opts>) + vim.lsp.enable(<name>)
-- old: require('lspconfig')[name].setup(<opts>)
----------------------------------------------------------------------
local function lsp_setup(server, opts)
  if vim.lsp and vim.lsp.enable and vim.lsp.config then
    -- Новый API
    vim.lsp.config(server, opts or {})
    vim.lsp.enable(server)
  else
    -- Старый API
    require("lspconfig")[server].setup(opts or {})
  end
end

----------------------------------------------------------------------
-- nvim-cmp (с защитой, если плагинов нет)
----------------------------------------------------------------------
local has_cmp, cmp = pcall(require, "cmp")
local has_luasnip, luasnip = pcall(require, "luasnip")

if has_cmp then
  cmp.setup({
    snippet = {
      expand = function(args)
        if has_luasnip then
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
      has_luasnip and { name = "luasnip" } or nil,
      { name = "path" },
    }),
  })
end

----------------------------------------------------------------------
-- CAPABILITIES (добавляем cmp, если он установлен)
----------------------------------------------------------------------
local capabilities = vim.lsp.protocol.make_client_capabilities()
local has_cmp_caps, cmp_lsp = pcall(require, "cmp_nvim_lsp")
if has_cmp_caps then
  capabilities = cmp_lsp.default_capabilities(capabilities)
end

----------------------------------------------------------------------
-- Диагностики + знаки
----------------------------------------------------------------------
local signs = {
  Error = "",
  Warn  = "",
  Hint  = "",
  Info  = "",
}
for type, icon in pairs(signs) do
  local hl = "DiagnosticSign" .. type
  vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = "" })
end

vim.diagnostic.config({
  virtual_text = false,
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = { border = "rounded", source = "always" },
})

----------------------------------------------------------------------
-- on_attach: buffer-local keymaps + inlay hints (если есть)
----------------------------------------------------------------------
local function on_attach(client, bufnr)
  local map = function(mode, lhs, rhs, desc)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true, desc = desc })
  end

  map("n", "gd", vim.lsp.buf.definition,            "LSP: Go to Definition")
  map("n", "K",  vim.lsp.buf.hover,                 "LSP: Hover")
  map("n", "gi", vim.lsp.buf.implementation,        "LSP: Go to Implementation")
  map("n", "<leader>rn", vim.lsp.buf.rename,        "LSP: Rename")
  map("n", "<leader>ca", vim.lsp.buf.code_action,   "LSP: Code Action")
  map("n", "[d", vim.diagnostic.goto_prev,          "LSP: Prev Diagnostic")
  map("n", "]d", vim.diagnostic.goto_next,          "LSP: Next Diagnostic")
  map("n", "<leader>q", vim.diagnostic.setloclist,  "LSP: Diagnostics to LocList")

  -- Neovim 0.10+ (и выше): inlay hints
  if vim.lsp.inlay_hint and vim.lsp.inlay_hint.enable then
    pcall(vim.lsp.inlay_hint.enable, true, { bufnr = bufnr })
  end
end

----------------------------------------------------------------------
-- Список серверов (как у тебя)
----------------------------------------------------------------------
local servers = {
  "bashls", "pyright", "terraformls", "solargraph", "yamlls", "dockerls",
  "ansiblels", "jsonls", "gopls",
}

-- Базовые опции для всех серверов
local base_opts = {
  capabilities = capabilities,
  on_attach = on_attach,
}

-- Инициализация серверов
for _, server in ipairs(servers) do
  lsp_setup(server, base_opts)
end

return M

