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
-- Ensure Mason binaries are on PATH (mode-aware)
----------------------------------------------------------------------
do
  local mason_utils = require("utils.mason")
  local mason_mode = mason_utils.resolve_mode()
  if mason_mode ~= "off" then
    local mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
    if vim.fn.isdirectory(mason_bin) == 1 then
      local path = vim.env.PATH or ""
      local sep = (vim.fn.has("win32") == 1) and ";" or ":"
      if not string.find(path, mason_bin, 1, true) then
        if mason_mode == "auto" then
          if path == "" then
            vim.env.PATH = mason_bin
          else
            vim.env.PATH = path .. sep .. mason_bin
          end
        else
          if path == "" then
            vim.env.PATH = mason_bin
          else
            vim.env.PATH = mason_bin .. sep .. path
          end
        end
      end
    end
  end
end

----------------------------------------------------------------------
-- Leaders (must be set before lazy / any plugins)
----------------------------------------------------------------------
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

----------------------------------------------------------------------
-- Basic options
----------------------------------------------------------------------
-- Set shell to bash if available (for better cross-platform compatibility)
if vim.fn.executable("bash") == 1 then
  vim.opt.shell = "bash"
end

vim.opt.termguicolors = true      -- enable truecolor before colorscheme
vim.opt.background = "dark"
vim.opt.number = true             -- show absolute line numbers
vim.opt.relativenumber = false    -- relative numbers (optional)

-- Diff tweaks (always add iwhite for less noise in diffs)
vim.opt.diffopt:append("iwhite")
