-- Notification helper with a quiet fallback for minimal Neovim setups.
local M = {}

M.levels = (vim.log and vim.log.levels) or { ERROR = "ERROR", INFO = "INFO", WARN = "WARN" }

function M.send(message, level)
  if vim.notify then
    vim.notify(message, level)
  else
    vim.api.nvim_echo({ { message } }, true, {})
  end
end

return M
