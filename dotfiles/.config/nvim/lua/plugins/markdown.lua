return {
  -- Markdown syntax / motions
  { "preservim/vim-markdown" },

  -- Live Markdown preview in browser
  {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown", "vimwiki" },
    cmd = { "MarkdownPreview", "MarkdownPreviewToggle", "MarkdownPreviewStop" },
    build = function()
      -- Only try to install if npm is available, for portability.
      if vim.fn.executable("npm") == 1 then
        -- Protect against "Unknown function: mkdp#util#install"
        pcall(function()
          vim.fn["mkdp#util#install"]()
        end)
      end
    end,
    init = function()
      vim.g.mkdp_filetypes = { "markdown", "vimwiki" }

      vim.g.mkdp_auto_start = 0
      vim.g.mkdp_auto_close = 1
    end,
  },
}
