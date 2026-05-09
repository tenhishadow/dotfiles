return {
  {
    "morhetz/gruvbox",
    lazy = false,
    priority = 1000,
    init = function()
      vim.g.gruvbox_guisp_fallback = "bg"
      vim.g.lightline = { colorscheme = "gruvbox" }
    end,
    config = function()
      vim.cmd("colorscheme gruvbox")
    end,
  },
  {
    "itchyny/lightline.vim",
    lazy = false,
  },
  { "tomasr/molokai", lazy = true },
  { "jacoborus/tender.vim", lazy = true },
}
