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

local langs = {
  "lua",
  "vim",
  "vimdoc",
  "query",
  "python",
  "bash",
  "yaml",
  "json",
  "markdown",
  "markdown_inline",
}

local task = install.install(langs, { summary = true })
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
