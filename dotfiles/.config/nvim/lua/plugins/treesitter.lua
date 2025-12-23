return {
  -- Treesitter for better syntax highlighting
  {
    "nvim-treesitter/nvim-treesitter",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      -- Try modern API first, then fall back to legacy
      local ok_modern, ts_config = pcall(require, "nvim-treesitter.config")
      local ok_legacy, ts_configs = pcall(require, "nvim-treesitter.configs")
      
      if not ok_modern and not ok_legacy then
        vim.notify("nvim-treesitter configuration module not found", vim.log.levels.WARN)
        return
      end

      local setup_config = {
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
      }

      -- Use the available API
      if ok_legacy then
        ts_configs.setup(setup_config)
      elseif ok_modern then
        ts_config.setup(setup_config)
      end
    end,
  },
}