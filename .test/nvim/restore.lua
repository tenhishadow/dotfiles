-- Exercise scheduled restores against real Git fixtures without network access.
local workspace = vim.fn.tempname()

local function read(path)
  local file = assert(io.open(path, "rb"))
  local contents = file:read("*a")
  file:close()
  return contents
end

local function write(path, contents)
  vim.fn.mkdir(vim.fn.fnamemodify(path, ":h"), "p")
  local file = assert(io.open(path, "wb"))
  assert(file:write(contents))
  assert(file:close())
end

local function command(args)
  local argv = { "env", "GIT_CONFIG_GLOBAL=/dev/null", "GIT_CONFIG_NOSYSTEM=1", "GIT_CONFIG_COUNT=0" }
  vim.list_extend(argv, args)
  local output = vim.fn.system(argv)
  assert(vim.v.shell_error == 0, table.concat(args, " ") .. "\n" .. output)
  return vim.trim(output)
end

local function git(path, ...)
  local args = { "git", "-C", path }
  vim.list_extend(args, { ... })
  return command(args)
end

local ok, err = xpcall(function()
  local expected_home = vim.fn.getcwd() .. "/.test/nvim/.home"
  assert(
    vim.fn.fnamemodify(vim.env.HOME, ":p") == vim.fn.fnamemodify(expected_home, ":p"),
    "Restore tests require the disposable Neovim HOME"
  )
  local source = vim.fn.getcwd() .. "/dotfiles/.config/nvim"
  assert(
    vim.fn.fnamemodify(vim.fn.stdpath("data"), ":p")
      == vim.fn.fnamemodify(vim.fn.getcwd() .. "/.test/nvim/.data/nvim", ":p"),
    "Restore tests require the disposable Neovim data directory"
  )
  local installed_lazy = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
  assert(vim.fn.isdirectory(installed_lazy .. "/.git") == 1, "Run the isolated cold restore first")
  local config = workspace .. "/config/nvim"
  local data = workspace .. "/data/nvim/lazy"
  local lazy_remote = workspace .. "/remotes/lazy.nvim"
  vim.fn.mkdir(workspace .. "/remotes", "p")
  vim.fn.mkdir(workspace .. "/home", "p")
  vim.fn.mkdir(data, "p")
  command({ "cp", "-a", installed_lazy, lazy_remote })
  git(lazy_remote, "remote", "set-url", "origin", "file://" .. lazy_remote)
  command({ "cp", "-a", lazy_remote, data .. "/lazy.nvim" })
  git(data .. "/lazy.nvim", "remote", "set-url", "origin", "https://github.com/folke/lazy.nvim.git")

  for _, path in ipairs({ "lua/config/lazy.lua", "lua/config/restore.lua", "lua/utils/text.lua" }) do
    write(config .. "/" .. path, read(source .. "/" .. path))
  end
  write(config .. "/init.lua", 'require("config.lazy")\n')
  local lock = {
    ["lazy.nvim"] = { branch = "main", commit = git(lazy_remote, "rev-parse", "HEAD") },
  }
  local newer = {}
  local specs = {}
  for _, name in ipairs({ "restore-alpha", "restore-beta" }) do
    local remote = workspace .. "/remotes/" .. name
    command({ "git", "init", "--quiet", "--initial-branch=main", remote })
    git(remote, "config", "user.name", "Neovim fixture")
    git(remote, "config", "user.email", "fixture@example.invalid")
    git(remote, "config", "commit.gpgsign", "false")
    write(remote .. "/fixture.txt", "pinned\n")
    git(remote, "add", "fixture.txt")
    git(remote, "commit", "--quiet", "-m", "Pinned fixture")
    lock[name] = { branch = "main", commit = git(remote, "rev-parse", "HEAD") }
    write(remote .. "/fixture.txt", "newer\n")
    git(remote, "commit", "--quiet", "-am", "Newer fixture")
    newer[name] = git(remote, "rev-parse", "HEAD")
    git(remote, "branch", "master")
    specs[#specs + 1] = ("{ name = %q, url = %q, lazy = true }"):format(name, "file://" .. remote)
  end
  write(config .. "/lua/plugins/init.lua", "return { " .. table.concat(specs, ", ") .. " }\n")
  local alpha = data .. "/restore-alpha"
  local beta = data .. "/restore-beta"
  command({ "git", "clone", "--quiet", "file://" .. workspace .. "/remotes/restore-alpha", alpha })
  git(alpha, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master")
  local lockfile = config .. "/lazy-lock.json"
  local original = vim.json.encode(lock) .. "\n"
  write(lockfile, original)

  local function restore(succeeds)
    local output = vim.fn.system({
      "env",
      "HOME=" .. workspace .. "/home",
      "XDG_CONFIG_HOME=" .. workspace .. "/config",
      "XDG_DATA_HOME=" .. workspace .. "/data",
      "XDG_STATE_HOME=" .. workspace .. "/state",
      "XDG_CACHE_HOME=" .. workspace .. "/cache",
      "NVIM_APPNAME=nvim",
      "NVIM_DOTFILES_RESTORE=1",
      "NVIM_DOTFILES_DISABLE_PLUGINS=0",
      "NVIM_USE_MASON=off",
      "GIT_CONFIG_GLOBAL=/dev/null",
      "GIT_CONFIG_NOSYSTEM=1",
      "GIT_CONFIG_COUNT=1",
      "GIT_CONFIG_KEY_0=url.file://" .. lazy_remote .. ".insteadOf",
      "GIT_CONFIG_VALUE_0=https://github.com/folke/lazy.nvim.git",
      "GIT_ALLOW_PROTOCOL=file",
      "timeout",
      "30s",
      vim.v.progpath,
      "--headless",
      "+lua require('config.restore').run()",
      "+cquit",
    })
    local status = vim.v.shell_error
    assert(status ~= 124, "Restore fixture timed out:\n" .. output)
    assert((status == 0) == succeeds, "Unexpected restore exit " .. status .. ":\n" .. output)
  end

  restore(true)
  assert(read(lockfile) == original, "Warm restore rewrote canonical lock metadata")
  assert(git(alpha, "rev-parse", "HEAD") == lock["restore-alpha"].commit, "Installed drift was retained")
  assert(git(beta, "rev-parse", "HEAD") == lock["restore-beta"].commit, "Missing plugin used a newer commit")
  restore(true)
  assert(read(lockfile) == original, "Repeated restore rewrote the canonical lock")

  git(alpha, "checkout", "--quiet", "--detach", newer["restore-alpha"])
  assert(vim.fn.delete(beta, "rf") == 0)
  local plugin_specs = read(config .. "/lua/plugins/init.lua")
  write(config .. "/lua/plugins/init.lua", "return { invalid Lua\n")
  restore(false)
  assert(read(lockfile) == original, "Invalid plugin specs rewrote the canonical lock")
  assert(git(alpha, "rev-parse", "HEAD") == newer["restore-alpha"], "Invalid specs changed installed plugins")
  assert(vim.fn.isdirectory(beta) == 0, "Invalid specs installed a plugin")
  write(config .. "/lua/plugins/init.lua", plugin_specs)

  assert(vim.fn.delete(lockfile) == 0)
  restore(false)
  assert(vim.fn.filereadable(lockfile) == 0, "Missing canonical lockfile was generated")
  assert(vim.fn.isdirectory(beta) == 0, "Missing lockfile installed an unpinned plugin")
  local missing_pin = vim.deepcopy(lock)
  missing_pin["restore-beta"] = nil
  local malformed_pin = vim.deepcopy(lock)
  malformed_pin["restore-beta"].commit = "invalid"
  local missing_bootstrap = vim.deepcopy(lock)
  missing_bootstrap["lazy.nvim"] = nil
  for _, contents in ipairs({
    "{ invalid json\n",
    vim.json.encode(missing_pin),
    vim.json.encode(malformed_pin),
    vim.json.encode(missing_bootstrap),
  }) do
    write(lockfile, contents)
    restore(false)
    assert(read(lockfile) == contents, "Rejected lockfile was rewritten")
    assert(git(alpha, "rev-parse", "HEAD") == newer["restore-alpha"], "Invalid pins changed installed plugins")
    assert(vim.fn.isdirectory(beta) == 0, "Invalid pins installed an unpinned plugin")
  end

  local unavailable = vim.deepcopy(lock)
  unavailable["restore-beta"].commit = string.rep("0", 40)
  local unavailable_contents = vim.json.encode(unavailable)
  write(lockfile, unavailable_contents)
  restore(false)
  assert(read(lockfile) == unavailable_contents, "Failed Git checkout rewrote the canonical lock")

  assert(vim.fn.delete(config .. "/init.lua") == 0)
  assert(vim.fn.delete(config .. "/lua/config/restore.lua") == 0)
  restore(false)
  assert(read(lockfile) == unavailable_contents, "Missing restore module changed the canonical lock")
end, debug.traceback)

vim.fn.delete(workspace, "rf")
if not ok then
  vim.api.nvim_err_writeln(err)
  vim.cmd.cquit(1)
end
print("Pinned restore regressions passed without network access")
vim.cmd.qa()
