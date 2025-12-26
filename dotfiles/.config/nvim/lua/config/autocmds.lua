-- lua/config/autocmds.lua
-- Autocommands and events

----------------------------------------------------------------------
-- Create augroup for user config
----------------------------------------------------------------------
local group = vim.api.nvim_create_augroup("UserConfig", { clear = false })

----------------------------------------------------------------------
-- Restore cursor position when reopening files
----------------------------------------------------------------------
vim.api.nvim_create_autocmd("BufReadPost", {
  group = group,
  desc = "Restore cursor position",
  callback = function(args)
    local bufnr = args.buf

    -- Only for real files (no help, no terminals, no special buffers)
    if vim.bo[bufnr].buftype ~= "" then
      return
    end

    -- Skip certain filetypes (git commit messages etc.), if you want
    if vim.bo[bufnr].filetype == "gitcommit" then
      return
    end

    -- Last cursor position mark
    local mark = vim.api.nvim_buf_get_mark(bufnr, '"')
    local lcount = vim.api.nvim_buf_line_count(bufnr)

    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})
