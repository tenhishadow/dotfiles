local languages = require("config.languages")

return {
  {
    "mfussenegger/nvim-lint",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      local lint = require("lint")
      lint.linters_by_ft = {}

      local auto_linters = languages.auto_linters_by_ft or languages.linters_by_ft
      local manual_linters = languages.manual_linters_by_ft or {}
      local log_levels = (vim.log and vim.log.levels) or { INFO = "INFO", WARN = "WARN" }

      local function notify(message, level)
        if vim.notify then
          vim.notify(message, level)
        else
          vim.api.nvim_echo({ { message } }, true, {})
        end
      end

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

      local function should_lint(bufnr)
        return vim.bo[bufnr].buftype == ""
          and vim.bo[bufnr].modifiable
          and vim.api.nvim_buf_get_name(bufnr) ~= ""
      end

      for filetype, linters in pairs(auto_linters) do
        for _, spec in ipairs(linters) do
          enable(filetype, spec.name, spec.cmd)
        end
      end

      local group = vim.api.nvim_create_augroup("dotfiles_lint", { clear = true })
      vim.api.nvim_create_autocmd("BufWritePost", {
        group = group,
        callback = function(args)
          if should_lint(args.buf) then
            pcall(lint.try_lint)
          end
        end,
      })

      local function filetype_keys(filetype)
        local keys = { filetype }
        local prefix, suffix = filetype:match("^([^.]+)%.(.+)$")
        if prefix then
          table.insert(keys, prefix)
          table.insert(keys, suffix)
        end
        return keys
      end

      local function collect_manual_linters(filetype)
        local names = {}
        local seen = {}

        for _, key in ipairs(filetype_keys(filetype or "")) do
          for _, spec in ipairs(manual_linters[key] or {}) do
            if not seen[spec.name] and vim.fn.executable(spec.cmd or spec.name) == 1 then
              table.insert(names, spec.name)
              seen[spec.name] = true
            end
          end
        end

        return names
      end

      local function complete_manual_linters(arg_lead)
        local names = {}
        local seen = {}

        for _, linters in pairs(manual_linters) do
          for _, spec in ipairs(linters) do
            if not seen[spec.name] and spec.name:find(arg_lead, 1, true) == 1 then
              table.insert(names, spec.name)
              seen[spec.name] = true
            end
          end
        end

        table.sort(names)
        return names
      end

      vim.api.nvim_create_user_command("DotfilesLintManual", function(opts)
        local names = {}

        if opts.args ~= "" then
          for name in opts.args:gmatch("[^,%s]+") do
            table.insert(names, name)
          end
        else
          names = collect_manual_linters(vim.bo.filetype)
        end

        if #names == 0 then
          notify("No available manual linters for this filetype", log_levels.INFO)
          return
        end

        local ok, err = pcall(lint.try_lint, names)
        if not ok then
          notify("Manual lint failed: " .. tostring(err), log_levels.WARN)
        end
      end, {
        nargs = "*",
        complete = complete_manual_linters,
        desc = "Run manual linters for the current filetype",
      })
    end,
  },
}
