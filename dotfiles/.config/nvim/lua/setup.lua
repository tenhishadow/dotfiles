-- lua/setup.lua
-- Plugin manager bootstrap and configuration

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
