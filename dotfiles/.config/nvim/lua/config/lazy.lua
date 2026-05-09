-- lazy.nvim bootstrap and plugin loading.

local lazy_name = "lazy.nvim"
local lazy_repo = "https://github.com/folke/lazy.nvim.git"
local lazy_path = vim.fn.stdpath("data") .. "/lazy/" .. lazy_name
local lazy_lockfile = vim.fn.stdpath("config") .. "/lazy-lock.json"
local text = require("utils.text")

local function has_ui()
  return #vim.api.nvim_list_uis() > 0
end

local function bootstrap_error(message, output)
  local lines = {
    { message .. "\n", "ErrorMsg" },
  }

  if output and output ~= "" then
    table.insert(lines, { output, "WarningMsg" })
  end

  if has_ui() then
    table.insert(lines, { "\nPress any key to exit..." })
  end

  vim.api.nvim_echo(lines, true, {})

  if has_ui() then
    vim.fn.getchar()
  end

  os.exit(1)
end

local function run_git(args)
  local output = vim.fn.system(args)
  if vim.v.shell_error ~= 0 then
    return false, output
  end
  return true, text.trim(output)
end

local function read_lazy_commit()
  local ok, lines = pcall(vim.fn.readfile, lazy_lockfile)
  if not ok or #lines == 0 then
    return nil
  end

  local ok_json, lock = pcall(vim.fn.json_decode, table.concat(lines, "\n"))
  if not ok_json or type(lock) ~= "table" then
    return nil
  end

  local lazy_lock = lock[lazy_name]
  if type(lazy_lock) ~= "table" or type(lazy_lock.commit) ~= "string" then
    return nil
  end

  local commit = text.trim(lazy_lock.commit)
  if commit == "" then
    return nil
  end

  return commit
end

local function fs_stat(path)
  return (vim.uv or vim.loop).fs_stat(path)
end

local lazy_commit = read_lazy_commit()

if not fs_stat(lazy_path) then
  local clone_args = {
    "git",
    "clone",
    "--filter=blob:none",
  }

  if not lazy_commit then
    table.insert(clone_args, "--branch=stable")
  end

  table.insert(clone_args, lazy_repo)
  table.insert(clone_args, lazy_path)

  local ok, output = run_git(clone_args)
  if not ok then
    bootstrap_error("Failed to clone lazy.nvim:", output)
  end
end

if lazy_commit then
  local ok, current_commit = run_git({ "git", "-C", lazy_path, "rev-parse", "HEAD" })
  if not ok then
    bootstrap_error("Failed to inspect lazy.nvim checkout:", current_commit)
  end

  if current_commit ~= lazy_commit then
    local checkout_ok, checkout_output = run_git({
      "git",
      "-C",
      lazy_path,
      "checkout",
      "--detach",
      "--quiet",
      lazy_commit,
    })

    if not checkout_ok then
      local fetch_ok, fetch_output = run_git({
        "git",
        "-C",
        lazy_path,
        "fetch",
        "--filter=blob:none",
        "origin",
        "+refs/heads/*:refs/remotes/origin/*",
      })

      if not fetch_ok then
        bootstrap_error("Failed to fetch pinned lazy.nvim commit:", fetch_output)
      end

      checkout_ok, checkout_output = run_git({
        "git",
        "-C",
        lazy_path,
        "checkout",
        "--detach",
        "--quiet",
        lazy_commit,
      })

      if not checkout_ok then
        bootstrap_error("Failed to checkout pinned lazy.nvim commit:", checkout_output)
      end
    end
  end
end

if not fs_stat(lazy_path .. "/lua/lazy/init.lua") then
  bootstrap_error("lazy.nvim bootstrap checkout is incomplete:", lazy_path)
end

vim.opt.rtp:prepend(lazy_path)

require("lazy").setup("plugins", {
  lockfile = lazy_lockfile,
  local_spec = false,
  install = {
    missing = true,
    colorscheme = { "gruvbox", "habamax" },
  },
  checker = {
    enabled = false,
    notify = false,
  },
  change_detection = {
    enabled = true,
    notify = false,
  },
  pkg = {
    sources = { "lazy", "packspec" },
  },
  rocks = {
    enabled = false,
  },
  performance = {
    rtp = {
      disabled_plugins = {
        "gzip",
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
