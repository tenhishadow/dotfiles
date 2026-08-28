-- Prove that a startup .wiki buffer triggers Vimwiki without plugin ftdetect.

local errors = {}
local expected_path = vim.fn.fnamemodify(vim.fn.getcwd() .. "/.test/nvim/vimwiki/index.wiki", ":p")
local actual_path = vim.fn.fnamemodify(vim.api.nvim_buf_get_name(0), ":p")

if actual_path ~= expected_path then
  table.insert(errors, "Unexpected startup buffer: " .. actual_path)
end
if vim.bo.filetype ~= "vimwiki" then
  table.insert(errors, "Startup .wiki filetype is " .. vim.bo.filetype)
end

local ok_lazy_config, lazy_config = pcall(require, "lazy.core.config")
local plugin = ok_lazy_config and lazy_config.plugins.vimwiki or nil
if not plugin or not (plugin._ and plugin._.loaded) then
  table.insert(errors, "Startup .wiki buffer did not load Vimwiki")
end
if vim.fn.exists(":VimwikiIndex") == 0 then
  table.insert(errors, "VimwikiIndex command is unavailable after first-buffer load")
end

if #errors > 0 then
  for _, message in ipairs(errors) do
    vim.api.nvim_echo({ { message } }, true, {})
  end
  vim.cmd("cq")
else
  vim.api.nvim_echo({ { "Vimwiki first-buffer OK" } }, true, {})
  vim.cmd("qa")
end
