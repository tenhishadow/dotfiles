return {
  -- Which-key for command discoverability
  {
    "folke/which-key.nvim",
    event = "VeryLazy", -- Lazy load to avoid startup cost
    config = function()
      local wk = require("which-key")
      
      wk.setup({
        -- Modern which-key v3 configuration
        preset = "modern",
        delay = 1000,
        
        -- Plugin configuration
        plugins = {
          marks = true,
          registers = true,
          spelling = {
            enabled = true,
            suggestions = 20,
          },
          presets = {
            operators = false,
            motions = true,
            text_objects = true,
            windows = true,
            nav = true,
            z = true,
            g = true,
          },
        },
        
        -- Window configuration (modern format)
        win = {
          border = "rounded",
          position = "bottom",
          margin = { 1, 0, 1, 0 },
          padding = { 2, 2, 2, 2 },
          winblend = 0,
        },
        
        layout = {
          height = { min = 4, max = 25 },
          width = { min = 20, max = 50 },
          spacing = 3,
          align = "left",
        },
        
        -- Modern filter instead of ignore_missing
        filter = function(mapping)
          -- Filter out hidden mappings
          return not vim.tbl_contains({ "<silent>", "<cmd>", "<Cmd>", "<CR>", "call", "lua", "^:", "^ " }, mapping.lhs)
        end,
        
        show_help = true,
        show_keys = true,
        
        disable = {
          buftypes = {},
          filetypes = { "TelescopePrompt" },
        },
      })

      -- Register key mappings using modern spec format
      wk.add({
        { "<leader>f", group = "find" },
        { "<leader>ff", desc = "Find files" },
        { "<leader>fb", desc = "Find buffers" },
        { "<leader>fg", desc = "Find git files" },
        { "<leader>fl", desc = "Find lines" },
        { "<leader>g", group = "git" },
        { "<leader>l", group = "lsp" },
        { "g", group = "goto" },
        { "]", group = "next" },
        { "[", group = "prev" },
      })
    end,
  },
}