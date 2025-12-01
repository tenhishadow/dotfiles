return {
  -- Markdown syntax / motions
  { "preservim/vim-markdown" },

  -- Live Markdown preview in browser
  {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown", "vimwiki" },
    build = function()
      -- Only try to install if npm is available, for portability.
      if vim.fn.executable("npm") == 1 then
        vim.fn["mkdp#util#install"]()
      end
    end,
    init = function()
      vim.g.mkdp_filetypes = { "markdown", "vimwiki" }
    end,
  },
}
