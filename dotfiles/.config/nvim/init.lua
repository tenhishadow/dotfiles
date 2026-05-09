-- init.lua
-- Minimal entry point: core setup, plugins, then optional user customizations.

-- Enable Lua module caching when available (faster startup).
pcall(function()
  if vim.loader and vim.loader.enable then
    vim.loader.enable()
  end
end)

local keymaps = require("config.keymaps_spec")

vim.g.mapleader = keymaps.leader.value
vim.g.maplocalleader = keymaps.localleader.value

local function safe_require(module)
  local ok, err = pcall(require, module)
  if not ok then
    vim.api.nvim_err_writeln(("Failed to load %s: %s"):format(module, err))
  end
  return ok
end

safe_require("config.options")
safe_require("config.keymaps")
safe_require("config.autocmds")
safe_require("config.filetypes")
safe_require("config.folds")
safe_require("config.quickfix")

if vim.env.NVIM_DOTFILES_DISABLE_PLUGINS == "1" then
  vim.g.dotfiles_plugins_disabled = true
elseif vim.fn.has("nvim-0.8") == 1 then
  safe_require("config.lazy")
else
  vim.g.dotfiles_plugins_disabled = true
end

-- Optional user overrides (keymaps, autocmds, etc.)
pcall(require, "custom")
