return {
  {
    "mbbill/undotree",
    cmd = { "UndotreeToggle", "UndotreeShow" },
  },
  {
    "junegunn/fzf",
    lazy = true,
  },
  {
    "junegunn/fzf.vim",
    dependencies = { "junegunn/fzf" },
    keys = {
      { "<leader>ff", ":Files<CR>", desc = "FZF Files" },
      { "<leader>fb", ":Buffers<CR>", desc = "FZF Buffers" },
      { "<leader>fg", ":GFiles<CR>", desc = "FZF Git files" },
      { "<leader>fl", ":Lines<CR>", desc = "FZF Lines" },
    },
  },
  {
    "vimwiki/vimwiki",
    ft = { "vimwiki" },
  },
  { "nvim-lua/plenary.nvim", lazy = true },
}
