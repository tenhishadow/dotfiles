return {

  { -- Linting
    'mfussenegger/nvim-lint',
    event = { 'BufReadPre', 'BufNewFile' },
    config = function()
      local lint = require 'lint'

      -------------------------------------------------------------------
      -- Start from a clean mapping and explicitly opt in the linters
      -- that are relevant for DevOps / DevSecOps / Python / data work.
      -------------------------------------------------------------------
      lint.linters_by_ft = {}

      -------------------------------------------------------------------
      -- Helper: register a linter only if its executable is available.
      -------------------------------------------------------------------
      local function enable(ft, linter, cmd)
        cmd = cmd or linter
        if vim.fn.executable(cmd) == 1 then
          local current = lint.linters_by_ft[ft] or {}
          table.insert(current, linter)
          lint.linters_by_ft[ft] = current
        end
      end

      -------------------------------------------------------------------
      -- Markdown via markdownlint-cli2
      -------------------------------------------------------------------
      if vim.fn.executable('markdownlint-cli2') == 1 then
        local ml = lint.linters.markdownlint or require('lint.linters.markdownlint')
        ml.cmd = 'markdownlint-cli2'
        lint.linters.markdownlint = ml
        enable('markdown', 'markdownlint', 'markdownlint-cli2')
      end

      -------------------------------------------------------------------
      -- Python
      -------------------------------------------------------------------
      enable('python', 'ruff', 'ruff')

      -------------------------------------------------------------------
      -- Shell / Bash / Zsh
      -------------------------------------------------------------------
      enable('sh',   'shellcheck', 'shellcheck')
      enable('bash', 'shellcheck', 'shellcheck')
      enable('zsh',  'shellcheck', 'shellcheck')

      -------------------------------------------------------------------
      -- YAML / Ansible
      -------------------------------------------------------------------
      enable('yaml',    'yamllint',     'yamllint')
      enable('ansible', 'ansible_lint', 'ansible-lint')

      -------------------------------------------------------------------
      -- Docker / containers
      -------------------------------------------------------------------
      enable('dockerfile', 'hadolint', 'hadolint')

      -------------------------------------------------------------------
      -- Terraform / HCL / Terragrunt
      -------------------------------------------------------------------
      enable('terraform', 'tflint', 'tflint')
      enable('hcl',       'tflint', 'tflint')

      -------------------------------------------------------------------
      -- JSON (lint) – keep it simple with jsonlint.
      -- Biome is used as a *formatter* via conform.nvim instead.
      -------------------------------------------------------------------
      enable('json', 'jsonlint', 'jsonlint')

      -------------------------------------------------------------------
      -- Lua (for Neovim config / tools)
      -------------------------------------------------------------------
      enable('lua', 'luacheck', 'luacheck')

      -------------------------------------------------------------------
      -- SQL / data engineering
      -------------------------------------------------------------------
      enable('sql', 'sqlfluff', 'sqlfluff')

      -------------------------------------------------------------------
      -- GitLab and other special linters
      --
      -- You can register custom linters here, for example wrapping
      -- `glab ci lint` or GitLab API calls, then opt them in via
      --   enable('yaml', 'gitlab_ci', 'your-binary')
      -------------------------------------------------------------------

      local lint_augroup = vim.api.nvim_create_augroup('lint', { clear = true })

      vim.api.nvim_create_autocmd({ 'BufEnter', 'BufWritePost', 'InsertLeave' }, {
        group = lint_augroup,
        callback = function()
          if vim.bo.modifiable then
            lint.try_lint()
          end
        end,
      })
    end,
  },
}
