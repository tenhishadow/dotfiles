-- init.lua
-- Minimal entry point: core setup, filetypes/folds, LSP, then optional user customizations.

require('config.options')
require('config.keymaps')
require('config.autocmds')
require('setup')
require('ft')
require('fold')
require('lsp')

-- Optional user overrides (keymaps, autocmds, etc.)
pcall(require, 'custom')
