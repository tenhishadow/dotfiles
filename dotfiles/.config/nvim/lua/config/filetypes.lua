-- Project-specific filetype detection.

if vim.filetype and vim.filetype.add then
  vim.filetype.add({
    pattern = {
      [".*%.hcl"] = "hcl",
      [".*%.tf"] = "terraform",
      [".*%.tofu"] = "terraform",
      [".*%.tfbackend"] = "hcl",
      [".*%.tfstate"] = "json",
      [".*%.tfstate%.backup"] = "json",
      [".*%.tftest%.hcl"] = "terraform",
      [".*%.tofutest%.hcl"] = "terraform",
      [".*%.tfvars"] = "terraform",
      [".*/%.terragrunt%.hcl"] = "terraform",
      [".*/root%.hcl"] = "terraform",
      [".*/terragrunt%.hcl"] = "terraform",
      [".*%.rsc"] = "rsc",
      [".*%.nginx"] = "nginx",
      [".*nginx%.conf"] = "nginx",
    },
    filename = {
      [".terraformrc"] = "hcl",
      ["terraform.rc"] = "hcl",
      ["Vagrantfile"] = "ruby",
      ["vagrantfile"] = "ruby",
    },
  })
end

local group = vim.api.nvim_create_augroup("dotfiles_filetypes", { clear = true })

local function set_buffer_filetype(bufnr, filetype)
  if vim.bo[bufnr].filetype ~= filetype then
    vim.bo[bufnr].filetype = filetype
  end
end

local function set_filetype(patterns, filetype)
  vim.api.nvim_create_autocmd({ "BufRead", "BufReadPost", "BufNewFile" }, {
    group = group,
    pattern = patterns,
    desc = "Set " .. filetype .. " filetype",
    callback = function(args)
      set_buffer_filetype(args.buf, filetype)
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
        set_buffer_filetype(args.buf, filetype)
      end
    end,
  })
end

local function detect_cloudformation(bufnr)
  local line_count = math.min(vim.api.nvim_buf_line_count(bufnr), 300)
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, line_count, false)
  local score = 0
  local is_json = false

  local exact_markers = {
    "AWSTemplateFormatVersion",
    "AWS::AccountId",
    "AWS::NoValue",
    "AWS::Partition",
    "AWS::Region",
    "AWS::StackId",
    "AWS::StackName",
    "AWS::URLSuffix",
    "Fn::Base64",
    "Fn::FindInMap",
    "Fn::GetAtt",
    "Fn::ImportValue",
    "Fn::Join",
    "Fn::Select",
    "Fn::Sub",
    "Fn::Transform",
    "!FindInMap",
    "!GetAtt",
    "!ImportValue",
    "!Join",
    "!Ref",
    "!Select",
    "!Sub",
  }

  for _, line in ipairs(lines) do
    if line:match("^%s*{") then
      is_json = true
    end

    if line:find("AWSTemplateFormatVersion", 1, true) then
      score = score + 100
    end
    if line:match("AWS::[%w]+::[%w]+") then
      score = score + 5
    end

    for _, marker in ipairs(exact_markers) do
      if line:find(marker, 1, true) then
        score = score + 2
      end
    end

    if score > 10 then
      set_buffer_filetype(bufnr, is_json and "json.cloudformation" or "yaml.cloudformation")
      return
    end
  end
end

vim.api.nvim_create_autocmd({ "BufReadPost", "BufNewFile" }, {
  group = group,
  pattern = { "*.yaml", "*.yml", "*.json", "*.template" },
  desc = "Detect CloudFormation templates",
  callback = function(args)
    detect_cloudformation(args.buf)
  end,
})

set_filetype({
  "*.hcl",
  "*.tfbackend",
  ".terraformrc",
  "terraform.rc",
}, "hcl")

set_filetype({
  "*.tf",
  "*.tofu",
  "*.tfvars",
  "*.tftest.hcl",
  "*.tofutest.hcl",
}, "terraform")

set_filetype({
  "*.tfstate",
  "*.tfstate.backup",
}, "json")

set_filetype({
  "*.rsc",
}, "rsc")

set_filetype({
  "*.nginx",
  "nginx*.conf",
  "*nginx.conf",
  "*/etc/nginx/*",
  "*/usr/local/nginx/conf/*",
  "*/nginx/*.conf",
}, "nginx")

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

set_filetype_if_basename({
  "Vagrantfile",
  "vagrantfile",
}, "ruby")
