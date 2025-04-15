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
  "**/{defaults,handlers,meta,tasks,templates,tests,vars}/**/*.{yml,yaml}",
  "**/playbook*.{yml,yaml}",
}, "yaml.ansible")

-- fastlane
set_filetype({
  "**/playbook*.{yml,yaml}",
  "**/Appfile",
  "**/Fastfile*",
  "**/Matchfile"
}, "ruby")

-- autoformat on exit
vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = "*.tf",
  command = "!terraform fmt <afile>"
})
vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = "*.hcl",
  command = "!terragrunt hclfmt <afile>"
})
