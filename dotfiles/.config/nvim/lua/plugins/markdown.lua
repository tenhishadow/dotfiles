return {
  { "tpope/vim-markdown" },
  {
    "iamcco/markdown-preview.nvim",
    build = "cd app && npm install",
    ft = { "markdown", "vimwiki" },
    init = function()
      vim.g.mkdp_filetypes = { "markdown", "vimwiki" }
    end,
  },
}
