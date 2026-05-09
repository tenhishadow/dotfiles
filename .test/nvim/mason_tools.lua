-- Validate that the configured Mason tool list only contains registry packages.

local repo_root = vim.fn.getcwd()
vim.opt.runtimepath:prepend(repo_root .. "/dotfiles/.config/nvim")

local languages = require("config.languages")
local errors = {}

local function add_error(message)
  table.insert(errors, message)
end

local function check_sorted_unique(values, label)
  local seen = {}
  local previous = nil

  for _, value in ipairs(values or {}) do
    if seen[value] then
      add_error(label .. " contains duplicate entry: " .. value)
    end
    seen[value] = true

    if previous and value < previous then
      add_error(label .. " is not sorted: " .. previous .. " before " .. value)
    end
    previous = value
  end
end

local function registry_package_exists(package_name)
  local url = ("https://raw.githubusercontent.com/mason-org/mason-registry/main/packages/%s/package.yaml"):format(package_name)
  vim.fn.system({ "curl", "-fsI", url })
  return vim.v.shell_error == 0
end

if vim.fn.executable("curl") ~= 1 then
  add_error("curl is required to validate Mason registry package names")
else
  check_sorted_unique(languages.mason_tools, "languages.mason_tools")

  for _, package_name in ipairs(languages.mason_tools or {}) do
    if not registry_package_exists(package_name) then
      add_error("Mason registry package not found: " .. package_name)
    end
  end
end

if #errors > 0 then
  for _, message in ipairs(errors) do
    vim.api.nvim_echo({ { message } }, true, {})
  end
  vim.cmd("cq")
else
  vim.api.nvim_echo({ { "Mason tools OK" } }, true, {})
  vim.cmd("qa")
end
