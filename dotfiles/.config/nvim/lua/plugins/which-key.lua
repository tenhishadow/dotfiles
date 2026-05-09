local keymaps = require("config.keymaps_spec")

return {
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      preset = "modern",
      delay = 1000,
    },
    config = function(_, opts)
      local wk = require("which-key")
      wk.setup(opts)
      wk.add(keymaps.which_key_groups)
    end,
  },
}
