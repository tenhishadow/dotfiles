-- Health checks for this dotfiles Neovim configuration.

local M = {}

local function health()
  if vim.health and vim.health.start then
    return vim.health
  end
  return {
    start = vim.fn["health#report_start"],
    ok = vim.fn["health#report_ok"],
    warn = vim.fn["health#report_warn"],
    error = vim.fn["health#report_error"],
    info = vim.fn["health#report_info"],
  }
end

local function has(version)
  return vim.fn.has("nvim-" .. version) == 1
end

local function check_version(h)
  local version = tostring(vim.version())
  if has("0.11.3") then
    h.ok("Neovim version: " .. version)
  elseif has("0.8") then
    h.warn("Neovim version: " .. version .. "; plugin layer works, modern LSP plugins are disabled")
  else
    h.warn("Neovim version: " .. version .. "; only the core config is loaded")
  end
end

local function has_any(cmds)
  for _, cmd in ipairs(cmds or {}) do
    if vim.fn.executable(cmd) == 1 then
      return true, cmd
    end
  end
  return false, nil
end

local function check_tool_sections(h)
  local ok_languages, languages = pcall(require, "config.languages")
  if not ok_languages then
    h.warn("Tool inventory unavailable")
    return
  end

  for _, section in ipairs(languages.health_tools or {}) do
    h.start(section.section)
    for _, tool in ipairs(section.tools or {}) do
      local found, cmd = has_any(tool.commands)
      if found then
        h.ok(tool.label .. " found: " .. cmd)
      elseif tool.required then
        h.error(tool.label .. " is required but missing")
      else
        h.warn(tool.label .. " is missing; related features stay disabled or manual-only")
      end
    end
  end
end

local function check_treesitter_tools(h)
  local ok_languages, languages = pcall(require, "config.languages")
  if not ok_languages then
    h.warn("Tree-sitter tool requirements unavailable")
    return
  end

  for _, req in ipairs(languages.treesitter_install_requirements or {}) do
    local found, cmd = has_any(req.commands)
    if found then
      h.ok("Tree-sitter requirement found: " .. req.label .. " (" .. cmd .. ")")
    else
      h.warn("Tree-sitter parser installs need: " .. req.label)
    end
  end
end

function M.check()
  local h = health()
  h.start("dotfiles.nvim")
  h.info("Warnings are actionable only for features you intend to use on this host.")
  check_version(h)
  check_tool_sections(h)
  check_treesitter_tools(h)
end

return M
