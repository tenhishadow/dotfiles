-- lua/config/keymaps.lua
-- Global key mappings.

local keymaps = require("config.keymaps_spec")

local actions = {
  toggle_paste = ":set invpaste paste?<CR>",
}

for _, keymap in ipairs(keymaps.core) do
  local action = assert(actions[keymap.id], "Missing keymap action: " .. keymap.id)
  vim.keymap.set(keymap.mode, keymap.lhs, action, {
    desc = keymap.desc,
    silent = true,
  })
end
