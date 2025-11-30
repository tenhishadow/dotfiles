return {
  -- Statusline
  { "itchyny/lightline.vim" },

  -- Persistent undo visualizer
  {
    "mbbill/undotree",
    cmd = { "UndotreeToggle", "UndotreeShow" },
  },

  -- FZF core + vim integration
  {
    "junegunn/fzf",
    -- build = function()
    --   -- Build only if shell tools are available (for portability)
    --   if vim.fn.executable("bash") == 1 then
    --     vim.fn.system({ "./install", "--bin" })
    --   end
    -- end,
  },
  {
    "junegunn/fzf.vim",
    dependencies = { "junegunn/fzf" },
    keys = {
      { "<leader>ff", ":Files<CR>",   desc = "FZF Files" },
      { "<leader>fb", ":Buffers<CR>", desc = "FZF Buffers" },
      { "<leader>fg", ":GFiles<CR>",  desc = "FZF Git files" },
      { "<leader>fl", ":Lines<CR>",   desc = "FZF Lines" },
    },
  },

  -- Personal wiki / knowledge base
  {
    "vimwiki/vimwiki",
    ft = { "vimwiki" },
  },

  -- Common Lua helpers for many plugins
  { "nvim-lua/plenary.nvim", lazy = true },
}
