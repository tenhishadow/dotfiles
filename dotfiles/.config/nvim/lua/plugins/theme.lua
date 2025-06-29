return {
  {
    "morhetz/gruvbox",
    priority = 1000,
    config = function()
      vim.cmd("colorscheme gruvbox")
      vim.opt.background = "dark"
      vim.opt.termguicolors = true
      vim.g.gruvbox_guisp_fallback = "bg"
      vim.g.lightline = { colorscheme = "gruvbox" }
    end,
  },
  { "tomasr/molokai" },
  { "jacoborus/tender.vim" },
}
