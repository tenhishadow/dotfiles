-- lua/setup.lua
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
vim.opt.number = true          -- show absolute line numbers
vim.opt.relativenumber = false  -- relative numbers (optional)

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
  checker = {
    enabled = true,
    notify = false
  },

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

-- This module is executed for side effects; it does not need to return anything.
----------------------------------------------------------------------
-- Restore cursor position when reopening files
----------------------------------------------------------------------
vim.api.nvim_create_autocmd("BufReadPost", {
  callback = function(args)
    local bufnr = args.buf

    -- Only for real files (no help, no terminals, no special buffers)
    if vim.bo[bufnr].buftype ~= "" then
      return
    end

    -- Skip certain filetypes (git commit messages etc.), if you want
    if vim.bo[bufnr].filetype == "gitcommit" then
      return
    end

    -- Last cursor position mark
    local mark = vim.api.nvim_buf_get_mark(bufnr, '"')
    local lcount = vim.api.nvim_buf_line_count(bufnr)

    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})
