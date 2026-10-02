if vim.fn.has("nvim-0.12") == 0 then
  return {}
end

return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    config = function()
      require("nvim-treesitter").setup()

      vim.treesitter.language.register("yaml", {
        "yaml.kubernetes",
        "yaml.kustomize",
        "yaml.docker-compose",
        "yaml.gitlab",
        "yaml.github-actions",
        "yaml.helm-values",
      })
      vim.treesitter.language.register("terraform", {
        "terraform-vars",
        "opentofu",
        "opentofu-vars",
      })
      vim.treesitter.language.register("markdown", "vimwiki")

      vim.api.nvim_create_autocmd("FileType", {
        group = vim.api.nvim_create_augroup("dotfiles_treesitter", { clear = true }),
        callback = function(args)
          local bufnr = args.buf
          local size = vim.api.nvim_buf_get_offset(bufnr, vim.api.nvim_buf_line_count(bufnr))
          if size > 100 * 1024 then
            vim.treesitter.stop(bufnr)
            return
          end

          -- Parser installation remains an explicit action.
          if not pcall(vim.treesitter.start, bufnr) then
            return
          end

          local language = vim.treesitter.language.get_lang(vim.bo[bufnr].filetype)
          if language ~= "python" and language ~= "yaml" then
            vim.bo[bufnr].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
          end
        end,
      })
    end,
  },
}
