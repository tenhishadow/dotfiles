local M = {}

local lspconfig = require('lspconfig')
local cmp = require('cmp')

-- Autocomplete setup
cmp.setup({
  snippet = {
    expand = function(args)
      require('luasnip').lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<CR>'] = cmp.mapping.confirm({ select = true }),
  }),
  sources = cmp.config.sources({
    { name = 'nvim_lsp' },
    { name = 'luasnip' },
    { name = 'path' },
  }),
})

-- Capabilities for nvim-cmp
local capabilities = require('cmp_nvim_lsp').default_capabilities()

-- List of LSP servers you use
local servers = {
  'bashls', 'pyright', 'terraformls', 'solargraph', 'yamlls', 'dockerls',
  'ansiblels', 'jsonls', 'gopls'
}

-- Iterate and setup each server
for _, server in ipairs(servers) do
  lspconfig[server].setup { capabilities = capabilities }
end

-- Recommended LSP key mappings
vim.keymap.set('n', 'gd', vim.lsp.buf.definition)
vim.keymap.set('n', 'K', vim.lsp.buf.hover)
vim.keymap.set('n', 'gi', vim.lsp.buf.implementation)
vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename)
vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action)
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev)
vim.keymap.set('n', ']d', vim.diagnostic.goto_next)
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist)

-- Diagnostics configuration
vim.diagnostic.config({
  virtual_text = false,
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = { border = 'rounded', source = 'always' },
})

return M
