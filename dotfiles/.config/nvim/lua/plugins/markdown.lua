return {
  -- Markdown syntax / motions
  { "tpope/vim-markdown" },

  -- Live Markdown preview in browser
  {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown", "vimwiki" },
    build = function()
      -- Be conservative: only try to install if npm exists,
      -- so config works on barebones machines too.
      if vim.fn.executable("npm") == 1 then
        vim.fn.system("cd app && npm install")
      end
    end,
    init = function()
      vim.g.mkdp_filetypes = { "markdown", "vimwiki" }
    end,
  },
}
