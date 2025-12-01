-- init.lua
-- Core Neovim setup: undo directory, leaders, basic options, and lazy.nvim bootstrap.

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
-- Basic options that are useful before plugins
----------------------------------------------------------------------
vim.opt.shell = "bash"
vim.opt.termguicolors = true      -- enable truecolor before colorscheme
vim.opt.background = "dark"

----------------------------------------------------------------------
-- Bootstrap lazy.nvim
----------------------------------------------------------------------
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local out = vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "--branch=stable",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

----------------------------------------------------------------------
-- Plugins via lazy.nvim (single setup call)
----------------------------------------------------------------------
require("lazy").setup({
  spec = {
    -- Kickstart's plugin collection (neo-tree, gitsigns, lint, autopairs, etc.)
    { import = "kickstart.plugins" },

    -- Your own plugins split by domain (UI, LSP, DevOps, markdown, etc.)
    { import = "plugins" },
  },

  -- Keep plugins up to date in the background
  checker = { enabled = true },

  -- Reload config on change without spamming notifications
  change_detection = { enabled = true, notify = false },

  -- Fallback colorscheme while plugins are installing
  install = { colorscheme = { "habamax" } },
})

----------------------------------------------------------------------
-- Diff tweaks
----------------------------------------------------------------------
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end

----------------------------------------------------------------------
-- Simple global keymaps (not tied to specific plugins)
----------------------------------------------------------------------
vim.keymap.set("n", "<F2>", ":set invpaste paste?<CR>", { silent = true })

-- NOTE:
-- EasyAlign mappings are provided by the plugin spec in
-- lua/plugins/format.lua using:
--   { "ga", "<Plug>(EasyAlign)", mode = { "n", "x" }, remap = true }
-- so we do NOT remap them here.

-- No module return needed for init.lua; it is executed, not required.
