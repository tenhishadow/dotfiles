-- The scheduled restore consumes canonical pins without writing through their symlink.
local M = {}

local function validate_plugins()
  local config = require("lazy.core.config")
  assert(config.spec:report() == 0, "Cannot restore invalid plugin specs")
  for name, plugin in pairs(config.plugins) do
    if plugin.url then
      assert(M.pins[name], "Plugin has no restore pin: " .. name)
      assert(plugin.commit == M.pins[name].commit, "Restore commit spec was not applied: " .. name)
    end
  end
end

function M.prepare()
  local source = vim.fn.stdpath("config") .. "/lazy-lock.json"
  local lines = vim.fn.readfile(source)
  local pins = vim.json.decode(table.concat(lines, "\n"))
  assert(type(pins) == "table" and pins["lazy.nvim"], "Missing lazy.nvim restore pin")

  local spec = { { import = "plugins" } }
  for name, pin in pairs(pins) do
    assert(
      type(pin) == "table" and type(pin.commit) == "string" and #pin.commit == 40 and pin.commit:match("^%x+$"),
      "Invalid restore pin: " .. name
    )
    table.insert(spec, { name, commit = pin.commit, pin = false, optional = true })
  end
  M.pins = pins

  local lockfile = vim.fn.tempname()
  assert(vim.fn.writefile(lines, lockfile) == 0, "Cannot create restore lock snapshot")
  assert((vim.uv or vim.loop).fs_chmod(lockfile, 384)) -- 0600
  vim.api.nvim_create_autocmd("VimLeavePre", {
    once = true,
    callback = function()
      vim.fn.delete(lockfile)
    end,
  })
  vim.api.nvim_create_autocmd("User", {
    pattern = { "LazyPlugins", "LazyInstallPre", "LazyRestorePre" },
    callback = function()
      local ok, err = pcall(validate_plugins)
      if not ok then
        vim.api.nvim_err_writeln(err)
        vim.cmd.cquit(1)
      end
    end,
  })
  return spec, lockfile
end

local function check_tasks()
  for name, plugin in pairs(require("lazy.core.config").plugins) do
    assert(plugin._.installed, "Plugin was not installed: " .. name)
    for _, task in ipairs(plugin._.tasks or {}) do
      assert(not task:has_errors(), "Plugin restore failed: " .. name .. " (" .. task.name .. ")")
    end
  end
end

function M.run()
  local ok, err = xpcall(function()
    assert(M.pins, "Pinned restore requires NVIM_DOTFILES_RESTORE=1 and successful startup")
    validate_plugins()
    check_tasks()

    -- Missing-plugin installation can rewrite Lazy's snapshot with existing
    -- checkout drift. Use the immutable commit specs instead of that snapshot.
    require("lazy").restore({ wait = true, show = false, lockfile = false })
    check_tasks()

    for name, plugin in pairs(require("lazy.core.config").plugins) do
      if plugin.url then
        local commit = vim.fn.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" })
        assert(vim.v.shell_error == 0 and vim.trim(commit) == M.pins[name].commit, "Restore pin mismatch: " .. name)
      end
    end
    print("Restored Neovim plugins to canonical pins without changing the lockfile")
  end, debug.traceback)

  if not ok then
    vim.api.nvim_err_writeln(err)
    vim.cmd.cquit(1)
  end
  vim.cmd.qa()
end

return M
