-- Project-specific filetype detection.

if vim.filetype and vim.filetype.add then
  vim.filetype.add({
    pattern = {
      [".*/%.terragrunt%.hcl"] = "terraform",
      [".*/root%.hcl"] = "terraform",
      [".*/terragrunt%.hcl"] = "terraform",
    },
  })
end

local group = vim.api.nvim_create_augroup("dotfiles_filetypes", { clear = true })

local function set_filetype(patterns, filetype)
  vim.api.nvim_create_autocmd({ "BufRead", "BufReadPost", "BufNewFile" }, {
    group = group,
    pattern = patterns,
    desc = "Set " .. filetype .. " filetype",
    callback = function()
      vim.bo.filetype = filetype
    end,
  })
end

local function set_filetype_if_basename(basenames, filetype)
  local lookup = {}
  for _, name in ipairs(basenames) do
    lookup[name] = true
  end

  vim.api.nvim_create_autocmd("FileType", {
    group = group,
    pattern = "*",
    desc = "Override filetype by basename",
    callback = function(args)
      local basename = vim.fn.fnamemodify(vim.api.nvim_buf_get_name(args.buf), ":t")
      if lookup[basename] then
        vim.bo[args.buf].filetype = filetype
      end
    end,
  })
end

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

set_filetype({
  "**/Appfile",
  "**/Fastfile*",
  "**/Matchfile",
}, "ruby")

set_filetype({
  "**/.ansible-lint",
  "**/.kube/config",
  "**/.yamllint",
}, "yaml")

set_filetype({
  "**/.terragrunt.hcl",
  "**/root.hcl",
  "**/terragrunt.hcl",
}, "terraform")

set_filetype_if_basename({
  ".terragrunt.hcl",
  "root.hcl",
  "terragrunt.hcl",
}, "terraform")
