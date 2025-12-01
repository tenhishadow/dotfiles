-- utilities for Neovim config
local M = {}

-- simple mapping helper: map(mode, lhs, rhs, opts)
-- opts: { buffer = bufnr, silent = bool, desc = string }
M.map = function(mode, lhs, rhs, opts)
  opts = opts or {}
  if opts.buffer then
    local buf = opts.buffer
    vim.keymap.set(mode, lhs, rhs, { buffer = buf, noremap = true, silent = opts.silent ~= false, desc = opts.desc })
  else
    vim.keymap.set(mode, lhs, rhs, { noremap = true, silent = opts.silent ~= false, desc = opts.desc })
  end
end

-- safe require helper
M.safe_require = function(name)
  local ok, m = pcall(require, name)
  if ok then return m end
  return nil
end

return M
