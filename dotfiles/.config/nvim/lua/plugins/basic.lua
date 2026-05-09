local keymaps = require("config.keymaps_spec")

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
    keys = keymaps.to_lazy_keys(keymaps.find),
  },
  {
    "vimwiki/vimwiki",
    ft = { "vimwiki" },
  },
  { "nvim-lua/plenary.nvim", lazy = true },
}
