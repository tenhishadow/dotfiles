local M = {}

vim.opt.foldmethod = "syntax"
vim.opt.foldlevelstart = 1

vim.g.javaScript_fold     = 1
vim.g.perl_fold           = 1
vim.g.ruby_fold           = 1
vim.g.sh_fold_enabled     = 1
vim.g.vimsyn_folding      = "af"
vim.g.xml_syntax_folding  = 1

-- yaml
local custom_folds_group = vim.api.nvim_create_augroup("custom_folds", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = custom_folds_group,
  pattern = "yaml",
  callback = function()
    vim.opt_local.foldmethod = "marker"
    vim.opt_local.foldlevel = 0
  end,
})

return M
