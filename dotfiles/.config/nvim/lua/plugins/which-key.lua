return {
  -- Which-key for command discoverability
  {
    "folke/which-key.nvim",
    event = "VeryLazy", -- Lazy load to avoid startup cost
    config = function()
      local wk = require("which-key")

      wk.setup({
        preset = "modern",
        delay = 1000,
      })

      -- Register only basic groups for existing functionality
      wk.add({
        { "<leader>f", group = "find" },
        { "<leader>g", group = "git" },
        { "<leader>l", group = "lsp" },
      })
    end,
  },
}
