-- init.lua

local M = {}

-- ========= Undo dir =========
local undodir = vim.fn.stdpath('data') .. '/undodir'
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir  = undodir

-- ========= Leaders (ДОЛЖНЫ быть до lazy) =========
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- ========= Глобальные настройки, которые полезно дать ДО плагинов =========
vim.opt.shell = "bash"
vim.opt.termguicolors = true       -- один раз, до темы
vim.opt.background = "dark"

-- ========= Bootstrap lazy.nvim =========
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local out = vim.fn.system({
    "git","clone","--filter=blob:none","--branch=stable",
    "https://github.com/folke/lazy.nvim.git", lazypath
  })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar(); os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

-- ========= Плагины через lazy.nvim (ОДИН setup) =========
require("lazy").setup({
  spec = {
    -- Kickstart's plugin collection (neo-tree, gitsigns, lint, autopairs, etc.)
    { import = "kickstart.plugins" },

    -- User plugins split by domain (UI, LSP, DevOps, markdown, etc.)
    { import = "plugins" },
  },

  -- Keep plugins up to date (can be toggled off if it’s too chatty)
  checker = { enabled = true },

  -- Detect config changes and reload automatically without spamming notifications
  change_detection = { enabled = true, notify = false },

  -- Fallback colorscheme while plugins are installing
  install = { colorscheme = { "habamax" } },
})

-- ignore space in diff
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end

-- keymaps
vim.keymap.set('n', '<F2>', ':set invpaste paste?<CR>', { silent = true })
vim.keymap.set('x', 'ga', '<Plug>(EasyAlign)', {})
vim.keymap.set('n', 'ga', '<Plug>(EasyAlign)', {})

return M
