local M = {}

local function set_filetype(patterns, ft)
  vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
    pattern = patterns,
    callback = function()
      vim.bo.filetype = ft
    end,
  })
end

-- ansible
set_filetype({
  "**/roles/*/tasks/*.yml",
  "**/roles/*/handlers/*.yml",
  "**/roles/*/meta/*.yml",
  "**/roles/*/defaults/*.yml",
  "**/roles/*/templates/*.yml",
  "**/roles/*/tests/*.yml",
  "**/roles/*/vars/*.yml",
  "**/playbook*.{yml,yaml}",
}, "yaml.ansible")

-- fastlane
set_filetype({
  "**/Appfile",
  "**/Fastfile*",
  "**/Matchfile"
}, "ruby")

-- yaml
set_filetype({
  "**/.kube/config",
  "**/.yamllint",
  "**/.ansible-lint"
}, "yaml")


-- Terraform / HCL formatting is handled by conform.nvim (see plugins/format.lua).
-- If you prefer shell commands, you can reintroduce autocmds here guarded by executable() checks.

return M
