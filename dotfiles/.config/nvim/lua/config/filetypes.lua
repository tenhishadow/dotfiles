-- Project-specific filetype detection.

if vim.filetype and vim.filetype.add then
  vim.filetype.add({
    pattern = {
      [".*%.hcl"] = "hcl",
      [".*%.tf"] = "terraform",
      [".*%.tfbackend"] = "hcl",
      [".*%.tfstate"] = "json",
      [".*%.tfstate%.backup"] = "json",
      [".*%.tftest%.hcl"] = "terraform",
      [".*%.tofutest%.hcl"] = "terraform",
      [".*%.tfvars"] = "terraform-vars",
      [".*%.tofu"] = "opentofu",
      [".*%.tofuvars"] = "opentofu-vars",
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
      ["docker-compose.yaml"] = "yaml.docker-compose",
      ["docker-compose.yml"] = "yaml.docker-compose",
      ["compose.yaml"] = "yaml.docker-compose",
      ["compose.yml"] = "yaml.docker-compose",
      [".gitlab-ci.yaml"] = "yaml.gitlab",
      [".gitlab-ci.yml"] = "yaml.gitlab",
      ["kustomization.yaml"] = "yaml.kustomize",
      ["kustomization.yml"] = "yaml.kustomize",
      ["Kustomization"] = "yaml.kustomize",
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

local function set_filetype_if_extension(extensions, filetype)
  local lookup = {}
  for _, ext in ipairs(extensions) do
    lookup[ext] = true
  end

  vim.api.nvim_create_autocmd("FileType", {
    group = group,
    pattern = "*",
    desc = "Override filetype by extension",
    callback = function(args)
      local ext = vim.fn.fnamemodify(vim.api.nvim_buf_get_name(args.buf), ":e")
      if lookup[ext] then
        set_buffer_filetype(args.buf, filetype)
      end
    end,
  })
end

local function buffer_path(bufnr)
  return vim.api.nvim_buf_get_name(bufnr):gsub("\\", "/")
end

local function can_set_yaml_domain(bufnr)
  local ft = vim.bo[bufnr].filetype
  return ft == "" or ft == "yaml" or ft == "yml"
end

local function has_chart_root(path)
  local dir = vim.fn.fnamemodify(path, ":p:h")

  while dir and dir ~= "" do
    if vim.fn.filereadable(dir .. "/Chart.yaml") == 1 or vim.fn.filereadable(dir .. "/Chart.yml") == 1 then
      return true
    end

    local parent = vim.fn.fnamemodify(dir, ":h")
    if parent == dir then
      break
    end
    dir = parent
  end

  return false
end

local function file_has_markers(bufnr, markers)
  local line_count = math.min(vim.api.nvim_buf_line_count(bufnr), 300)
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, line_count, false)
  local found = {}

  for _, line in ipairs(lines) do
    for _, marker in ipairs(markers) do
      if line:find(marker, 1, true) then
        found[marker] = true
      end
    end
  end

  for _, marker in ipairs(markers) do
    if not found[marker] then
      return false
    end
  end

  return true
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
  "*.tftest.hcl",
  "*.tofutest.hcl",
}, "terraform")

set_filetype({
  "*.tfvars",
}, "terraform-vars")

set_filetype({
  "*.tofu",
}, "opentofu")

set_filetype({
  "*.tofuvars",
}, "opentofu-vars")

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
  "**/roles/*/tasks/*.yaml",
  "**/roles/*/handlers/*.yml",
  "**/roles/*/handlers/*.yaml",
  "**/roles/*/meta/*.yml",
  "**/roles/*/meta/*.yaml",
  "**/roles/*/defaults/*.yml",
  "**/roles/*/defaults/*.yaml",
  "**/roles/*/templates/*.yml",
  "**/roles/*/templates/*.yaml",
  "**/roles/*/tests/*.yml",
  "**/roles/*/tests/*.yaml",
  "**/roles/*/vars/*.yml",
  "**/roles/*/vars/*.yaml",
  "**/host_vars/*.yml",
  "**/host_vars/*.yaml",
  "**/host_vars/**/*.yml",
  "**/host_vars/**/*.yaml",
  "**/group_vars/*.yml",
  "**/group_vars/*.yaml",
  "**/group_vars/**/*.yml",
  "**/group_vars/**/*.yaml",
  "**/inventory/*.yml",
  "**/inventory/*.yaml",
  "**/inventory/**/*.yml",
  "**/inventory/**/*.yaml",
  "**/inventories/*.yml",
  "**/inventories/*.yaml",
  "**/inventories/**/*.yml",
  "**/inventories/**/*.yaml",
  "**/playbook*.yml",
  "**/playbook*.yaml",
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
  "**/.github/workflows/*.yaml",
  "**/.github/workflows/*.yml",
  "**/.forgejo/workflows/*.yaml",
  "**/.forgejo/workflows/*.yml",
  "**/.gitea/workflows/*.yaml",
  "**/.gitea/workflows/*.yml",
}, "yaml.github-actions")

set_filetype({
  "**/.gitlab-ci.yaml",
  "**/.gitlab-ci.yml",
  "**/.gitlab/*.yaml",
  "**/.gitlab/*.yml",
}, "yaml.gitlab")

set_filetype({
  "**/docker-compose.yaml",
  "**/docker-compose.yml",
  "**/compose.yaml",
  "**/compose.yml",
}, "yaml.docker-compose")

set_filetype({
  "**/kustomization.yaml",
  "**/kustomization.yml",
  "**/Kustomization",
}, "yaml.kustomize")

set_filetype({
  "**/k8s/**/*.yaml",
  "**/k8s/**/*.yml",
  "**/kubernetes/**/*.yaml",
  "**/kubernetes/**/*.yml",
  "**/manifests/**/*.yaml",
  "**/manifests/**/*.yml",
  "**/deploy/**/*.yaml",
  "**/deploy/**/*.yml",
  "**/deployments/**/*.yaml",
  "**/deployments/**/*.yml",
  "**/clusters/**/*.yaml",
  "**/clusters/**/*.yml",
  "**/apps/**/*.yaml",
  "**/apps/**/*.yml",
  "**/base/**/*.yaml",
  "**/base/**/*.yml",
  "**/overlays/**/*.yaml",
  "**/overlays/**/*.yml",
}, "yaml.kubernetes")

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

set_filetype_if_extension({ "tfvars" }, "terraform-vars")
set_filetype_if_extension({ "tofu" }, "opentofu")
set_filetype_if_extension({ "tofuvars" }, "opentofu-vars")

vim.api.nvim_create_autocmd({ "BufReadPost", "BufNewFile" }, {
  group = group,
  pattern = { "*.yaml", "*.yml", "*.tpl", "*.gotmpl" },
  desc = "Refine Kubernetes and Helm filetypes",
  callback = function(args)
    local path = buffer_path(args.buf)

    if path:match("/templates/") and has_chart_root(path) then
      set_buffer_filetype(args.buf, "helm")
      return
    end

    if path:match("/values[^/]*%.ya?ml$") and has_chart_root(path) then
      set_buffer_filetype(args.buf, "yaml.helm-values")
      return
    end

    if can_set_yaml_domain(args.buf) and file_has_markers(args.buf, { "apiVersion:", "kind:" }) then
      set_buffer_filetype(args.buf, "yaml.kubernetes")
    end
  end,
})
