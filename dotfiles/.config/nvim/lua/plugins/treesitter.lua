local languages = require("config.languages")

if vim.fn.has("nvim-0.10") == 0 then
  return {}
end

return {
  {
    "nvim-treesitter/nvim-treesitter",
    cmd = { "TSInstall", "TSInstallInfo", "TSUpdate", "TSUpdateSync" },
    event = { "BufReadPost", "BufNewFile" },
    opts = {
      ensure_installed = languages.treesitter,
      sync_install = false,
      auto_install = false,
      ignore_install = {},
      highlight = {
        enable = true,
        disable = function(_, buf)
          local max_filesize = 100 * 1024
          local name = vim.api.nvim_buf_get_name(buf)
          local ok_stat, stats = pcall((vim.uv or vim.loop).fs_stat, name)
          return ok_stat and stats and stats.size > max_filesize
        end,
        additional_vim_regex_highlighting = false,
      },
      indent = {
        enable = true,
        disable = { "python", "yaml" },
      },
    },
    config = function(_, opts)
      local ok_legacy, ts_configs = pcall(require, "nvim-treesitter.configs")
      if ok_legacy then
        ts_configs.setup(opts)
        return
      end

      local ok_modern, ts_config = pcall(require, "nvim-treesitter.config")
      if ok_modern and ts_config.setup then
        ts_config.setup(opts)
      else
        vim.notify("nvim-treesitter configuration module not found", vim.log.levels.WARN)
      end
    end,
  },
}
