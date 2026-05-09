local languages = require("config.languages")

return {
  {
    "mfussenegger/nvim-lint",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      local lint = require("lint")
      lint.linters_by_ft = {}

      local function enable(filetype, linter, cmd)
        if vim.fn.executable(cmd or linter) ~= 1 then
          return
        end

        local current = lint.linters_by_ft[filetype] or {}
        table.insert(current, linter)
        lint.linters_by_ft[filetype] = current
      end

      if vim.fn.executable("markdownlint-cli2") == 1 then
        local markdownlint = lint.linters.markdownlint or require("lint.linters.markdownlint")
        markdownlint.cmd = "markdownlint-cli2"
        lint.linters.markdownlint = markdownlint
      end

      for filetype, linters in pairs(languages.linters_by_ft) do
        for _, spec in ipairs(linters) do
          enable(filetype, spec.name, spec.cmd)
        end
      end

      local group = vim.api.nvim_create_augroup("dotfiles_lint", { clear = true })
      vim.api.nvim_create_autocmd({ "BufEnter", "BufWritePost", "InsertLeave" }, {
        group = group,
        callback = function()
          if vim.bo.modifiable then
            lint.try_lint()
          end
        end,
      })
    end,
  },
}
