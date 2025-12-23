-- lua/config/options.lua
-- Core Neovim options and settings

----------------------------------------------------------------------
-- Undo directory
----------------------------------------------------------------------
local undodir = vim.fn.stdpath("data") .. "/undodir"
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir = undodir

----------------------------------------------------------------------
-- Leaders (must be set before lazy / any plugins)
----------------------------------------------------------------------
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

----------------------------------------------------------------------
-- Basic options
----------------------------------------------------------------------
vim.opt.shell = "bash"
vim.opt.termguicolors = true      -- enable truecolor before colorscheme
vim.opt.background = "dark"
vim.opt.number = true             -- show absolute line numbers
vim.opt.relativenumber = false    -- relative numbers (optional)

-- Diff tweaks
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end