return {
  -- Treesitter for better syntax highlighting
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
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
          "terraform",
          "dockerfile",
          "gitignore",
          "gitcommit",
        },

        -- Install parsers synchronously (only applied to `ensure_installed`)
        sync_install = false,

        -- Automatically install missing parsers when entering buffer
        auto_install = true,

        -- List of parsers to ignore installing
        ignore_install = {},

        highlight = {
          enable = true,

          -- Disable for large files (performance)
          disable = function(lang, buf)
            local max_filesize = 100 * 1024 -- 100 KB
            local ok_stat, stats = pcall(vim.loop.fs_stat, vim.api.nvim_buf_get_name(buf))
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

        incremental_selection = {
          enable = true,
          keymaps = {
            init_selection = "<C-space>",
            node_incremental = "<C-space>",
            scope_incremental = "<C-s>",
            node_decremental = "<M-space>",
          },
        },
      })

      -- Enable folding based on treesitter (optional)
      vim.opt.foldmethod = "expr"
      vim.opt.foldexpr = "nvim_treesitter#foldexpr()"
      vim.opt.foldenable = false -- Start with folds open
    end,
  },
}