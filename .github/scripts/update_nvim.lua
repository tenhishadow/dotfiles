-- Run after the disposable config starts; never publish a partial plugin update.
local ok, err = xpcall(function()
  assert(vim.fn.has("nvim-0.11.3") == 1, "Plugin upgrades require Neovim 0.11.3 or newer")

  local config = require("lazy.core.config")
  local lock = vim.json.decode(table.concat(vim.fn.readfile(config.options.lockfile), "\n"))
  for name in pairs(lock) do
    assert(config.plugins[name], "Locked plugin was excluded from the upgrade: " .. name)
  end

  require("lazy").update({ wait = true, show = false })
  for name, plugin in pairs(config.plugins) do
    assert(plugin._.installed, "Plugin was not installed: " .. name)
    for _, task in ipairs(plugin._.tasks or {}) do
      assert(not task:has_errors(), "Plugin upgrade failed: " .. name .. " (" .. task.name .. ")")
    end
  end

  local mason_packages = vim.fn.glob(vim.fn.stdpath("data") .. "/mason/packages/*", false, true)
  assert(#mason_packages == 0, "Plugin upgrades must not install Mason tools")
  print("Updated all " .. vim.tbl_count(config.plugins) .. " Neovim plugins without installing Mason tools")
end, debug.traceback)

if not ok then
  vim.api.nvim_err_writeln(err)
  vim.cmd.cquit(1)
end
vim.cmd.qa()
