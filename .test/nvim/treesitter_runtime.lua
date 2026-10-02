-- Exercise highlighting with a bundled parser, without installing parsers.
return function(add_error)
  if vim.fn.has("nvim-0.12") == 0 then
    return
  end

  local original_buffer = vim.api.nvim_get_current_buf()
  local buffers = {}
  local indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"

  local function open_buffer(filetype, content)
    local bufnr = vim.api.nvim_create_buf(true, false)
    table.insert(buffers, bufnr)
    vim.api.nvim_set_current_buf(bufnr)
    vim.api.nvim_buf_set_name(bufnr, vim.fn.tempname() .. "." .. filetype)
    vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, { content })
    vim.bo[bufnr].filetype = filetype
    return bufnr
  end

  local small = open_buffer("c", "int main(void) { return 0; }")
  if not vim.treesitter.highlighter.active[small] then
    add_error("Tree-sitter did not highlight a buffer with a bundled parser")
  end
  if vim.bo[small].indentexpr ~= indentexpr then
    add_error("Tree-sitter indentation was not enabled")
  end

  local large = open_buffer("c", "/*" .. string.rep("x", 100 * 1024) .. "*/")
  if vim.treesitter.highlighter.active[large] then
    add_error("Tree-sitter highlighted a buffer larger than 100 KiB")
  end
  if vim.bo[large].indentexpr == indentexpr then
    add_error("Tree-sitter indentation was enabled for a buffer larger than 100 KiB")
  end

  local missing_ok, missing_error = pcall(open_buffer, "dotfiles_missing_parser", "no parser")
  if not missing_ok then
    add_error("A missing optional parser caused an error: " .. tostring(missing_error))
  end

  vim.api.nvim_set_current_buf(original_buffer)
  for _, bufnr in ipairs(buffers) do
    vim.api.nvim_buf_delete(bufnr, { force = true })
  end
end
