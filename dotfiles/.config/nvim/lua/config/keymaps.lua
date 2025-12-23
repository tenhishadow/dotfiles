-- lua/config/keymaps.lua
-- Key mappings

----------------------------------------------------------------------
-- Simple global keymaps (not tied to specific plugins)
----------------------------------------------------------------------
vim.keymap.set("n", "<F2>", ":set invpaste paste?<CR>", { silent = true })