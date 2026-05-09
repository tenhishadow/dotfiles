-- Small text helpers shared by core config modules.
local M = {}

function M.trim(value)
  return tostring(value or ""):gsub("^%s+", ""):gsub("%s+$", "")
end

return M
