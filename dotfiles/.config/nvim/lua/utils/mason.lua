-- utilities for Mason mode and auto-missing filtering
local M = {}

local function normalize(value)
  if value == nil then
    return ""
  end
  return tostring(value)
end

function M.resolve_mode(value)
  local v = normalize(value or vim.env.NVIM_USE_MASON)
  v = string.lower(v)
  if v == "1" or v == "true" or v == "always" or v == "yes" then
    return "always"
  end
  if v == "auto" or v == "missing" then
    return "auto"
  end
  return "off"
end

function M.filter_missing(pkgs, bin_map, is_exe)
  is_exe = is_exe or function(cmd)
    return vim.fn.executable(cmd) == 1
  end

  local missing = {}
  for _, pkg in ipairs(pkgs or {}) do
    local bins = bin_map and bin_map[pkg] or nil
    if type(bins) == "string" then
      bins = { bins }
    end
    if not bins or #bins == 0 then
      bins = { pkg }
    end
    local found = false
    for _, bin in ipairs(bins) do
      if is_exe(bin) then
        found = true
        break
      end
    end
    if not found then
      table.insert(missing, pkg)
    end
  end

  return missing
end

return M
