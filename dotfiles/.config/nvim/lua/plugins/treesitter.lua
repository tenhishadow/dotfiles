return {
  -- Treesitter for better syntax highlighting
  {
    "nvim-treesitter/nvim-treesitter",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      -- Check if treesitter configs module is available
      local ok, configs = pcall(require, "nvim-treesitter.configs")
      if not ok then
        vim.notify("nvim-treesitter.configs not found", vim.log.levels.WARN)
        return
      end

      configs.setup({
        -- Install parsers for common languages
        ensure_installed = {
          "lua",
          "vim",
          "vimdoc",
          "query",
          "python",
          "bash",
          "yaml",
          "json",
          "markdown",
          "markdown_inline",
        },

        -- Install parsers synchronously (only applied to `ensure_installed`)
        sync_install = false,

        -- Don't automatically install missing parsers (for reproducibility)
        auto_install = false,

        -- List of parsers to ignore installing
        ignore_install = {},

        highlight = {
          enable = true,

          -- Disable for large files (performance)
          disable = function(lang, buf)
            local max_filesize = 100 * 1024 -- 100 KB
            local ok_stat, stats = pcall((vim.uv or vim.loop).fs_stat, vim.api.nvim_buf_get_name(buf))
            if ok_stat and stats and stats.size > max_filesize then
              return true
            end
          end,

          -- Setting this to true will run `:h syntax` and tree-sitter at the same time.
          additional_vim_regex_highlighting = false,
        },

        indent = {
          enable = true,
          -- Disable for problematic languages
          disable = { "python", "yaml" },
        },
      })
    end,
  },
}