-- Core-only compatibility smoke for old-Neovim-style startup.

local errors = {}

local function add_error(msg)
  table.insert(errors, msg)
end

local function safe_require(name)
  local ok = pcall(require, name)
  if not ok then
    add_error("Failed to require " .. name)
  end
end

if not vim.g.dotfiles_plugins_disabled then
  add_error("Plugin layer was not disabled")
end

for _, module in ipairs({
  "config.options",
  "config.keymaps",
  "config.autocmds",
  "config.filetypes",
  "config.folds",
  "config.quickfix",
  "dotfiles.health",
}) do
  safe_require(module)
end

for _, command in ipairs({
  "DotfilesKubeconform",
  "DotfilesHelmLint",
  "DotfilesKustomizeBuild",
  "DotfilesTerraformValidate",
  "DotfilesTofuValidate",
  "DotfilesTrivyConfig",
  "DotfilesGitleaksDetect",
  "DotfilesSemgrep",
}) do
  if vim.fn.exists(":" .. command) <= 0 then
    add_error("Missing manual command: " .. command)
  end
end

if #errors > 0 then
  for _, msg in ipairs(errors) do
    vim.api.nvim_echo({ { msg } }, true, {})
  end
  vim.cmd("cq")
else
  vim.api.nvim_echo({ { "Compat OK" } }, true, {})
  vim.cmd("qa")
end
