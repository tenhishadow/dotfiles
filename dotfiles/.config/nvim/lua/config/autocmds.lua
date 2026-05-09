-- lua/config/autocmds.lua
-- Autocommands and events.

local group = vim.api.nvim_create_augroup("dotfiles_core", { clear = true })

vim.api.nvim_create_autocmd("BufReadPost", {
  group = group,
  desc = "Restore cursor position",
  callback = function(args)
    local bufnr = args.buf

    if vim.bo[bufnr].buftype ~= "" then
      return
    end

    if vim.bo[bufnr].filetype == "gitcommit" then
      return
    end

    local mark = vim.api.nvim_buf_get_mark(bufnr, '"')
    local lcount = vim.api.nvim_buf_line_count(bufnr)

    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})
