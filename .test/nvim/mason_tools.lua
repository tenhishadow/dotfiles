-- Validate the canonical Mason inventories against a pinned registry snapshot.

local repo_root = vim.fn.getcwd()
vim.opt.runtimepath:prepend(repo_root .. "/dotfiles/.config/nvim")

local languages = require("config.languages")
local snapshot = dofile(repo_root .. "/.test/nvim/mason_registry_snapshot.lua")
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

local function as_set(values)
  local result = {}
  for _, value in ipairs(values or {}) do
    result[value] = true
  end
  return result
end

if
  type(snapshot.registry_commit) ~= "string"
  or #snapshot.registry_commit ~= 40
  or not snapshot.registry_commit:match("^[0-9a-f]+$")
then
  add_error("Mason registry snapshot must identify an exact lowercase commit SHA")
end

check_sorted_unique(languages.mason_tools, "languages.mason_tools")
check_sorted_unique(languages.mason_lsp_servers, "languages.mason_lsp_servers")
check_sorted_unique(snapshot.packages, "snapshot.packages")

local package_set = as_set(snapshot.packages)
local server_set = as_set(languages.mason_lsp_servers)
local referenced_packages = {}

for _, package_name in ipairs(languages.mason_tools or {}) do
  referenced_packages[package_name] = true
  if not package_set[package_name] then
    add_error("Mason tool is absent from the pinned registry snapshot: " .. package_name)
  end
end

for _, server_name in ipairs(languages.mason_lsp_servers or {}) do
  local package_name = snapshot.lspconfig_to_package[server_name]

  if not languages.lsp_bins[server_name] then
    add_error("Mason LSP server has no executable inventory: " .. server_name)
  end
  if type(package_name) ~= "string" or package_name == "" then
    add_error("Mason LSP server has no pinned registry mapping: " .. server_name)
  else
    referenced_packages[package_name] = true
    if not package_set[package_name] then
      add_error("Mason LSP package is absent from the pinned registry snapshot: " .. package_name)
    end
  end
end

for server_name, _ in pairs(snapshot.lspconfig_to_package or {}) do
  if not server_set[server_name] then
    add_error("Pinned Mason LSP mapping is not configured: " .. server_name)
  end
end

for _, package_name in ipairs(snapshot.packages or {}) do
  if not referenced_packages[package_name] then
    add_error("Pinned Mason registry package is not referenced: " .. package_name)
  end
end

if #errors > 0 then
  for _, message in ipairs(errors) do
    vim.api.nvim_echo({ { message } }, true, {})
  end
  vim.cmd("cq")
else
  vim.api.nvim_echo({ { "Mason inventory OK" } }, true, {})
  vim.cmd("qa")
end
