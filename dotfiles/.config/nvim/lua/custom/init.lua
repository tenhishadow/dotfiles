-- lua/custom/init.lua
-- Entry point for user customizations: keymaps, autocmds and small helpers.
-- This is loaded after core setup so leader and core options are defined.

-- Load keymaps and autocmds (keeps them separate from plugin configs)
pcall(function() require('custom.keymaps') end)
pcall(function() require('custom.autocmds') end)

return {}

