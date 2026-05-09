-- Install required Tree-sitter parsers in a headless-safe way.

local ok_lazy, lazy = pcall(require, "lazy")
if ok_lazy and lazy and lazy.load then
  pcall(lazy.load, { plugins = { "nvim-treesitter" } })
end

local ok_install, install = pcall(require, "nvim-treesitter.install")
if not ok_install then
  error("nvim-treesitter.install not available")
end

local ok_config, ts_config = pcall(require, "nvim-treesitter.config")
if not ok_config then
  error("nvim-treesitter.config not available")
end

local ok_languages, languages = pcall(require, "config.languages")
if not ok_languages then
  error("config.languages not available")
end

local install_mode = vim.env.NVIM_TS_INSTALL or "auto"
install_mode = string.lower(install_mode)
if install_mode == "off" or install_mode == "0" or install_mode == "false" then
  return
end

local marker_ok = vim.fn.stdpath("state") .. "/treesitter_install_ok"
local marker_failed = vim.fn.stdpath("state") .. "/treesitter_install_failed"
if vim.fn.filereadable(marker_failed) == 1 and vim.env.NVIM_TS_FORCE ~= "1" then
  return
end

if install_mode == "auto" and vim.fn.filereadable(marker_ok) == 1 then
  return
end

local parser_dir = ts_config.get_install_dir("parser")
local existing = vim.fn.globpath(parser_dir, "*.so", 0, 1)
if install_mode == "auto" and existing and #existing > 0 then
  return
end

local function has_any(commands)
  for _, cmd in ipairs(commands or {}) do
    if vim.fn.executable(cmd) == 1 then
      return true
    end
  end
  return false
end

local missing = {}
for _, req in ipairs(languages.treesitter_install_requirements or {}) do
  if not has_any(req.commands) then
    table.insert(missing, req.label)
  end
end

if #missing > 0 then
  local message = "Tree-sitter parser install skipped; missing: " .. table.concat(missing, ", ")
  if install_mode == "auto" then
    vim.api.nvim_echo({ { message } }, true, {})
    return
  end
  error(message)
end

local task = install.install(languages.treesitter, { summary = true })
if task and task.wait then
  local timeout_ms = tonumber(vim.env.NVIM_TS_TIMEOUT_MS or "120000")
  local ok, success = pcall(task.wait, task, timeout_ms)
  if ok and success then
    vim.fn.writefile({ "ok" }, marker_ok)
    pcall(vim.fn.delete, marker_failed)
  else
    vim.fn.writefile({ "failed" }, marker_failed)
    pcall(vim.fn.delete, marker_ok)
  end
else
  vim.fn.writefile({ "failed" }, marker_failed)
  pcall(vim.fn.delete, marker_ok)
end
