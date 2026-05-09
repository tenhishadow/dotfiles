-- helpers for checking whether external commands exist and are runnable
local M = {}

local cache = {}

local default_probes = {
  -- Import/runtime breakage is common for the Python wrapper package, so
  -- treat it as unavailable unless a trivial invocation succeeds.
  ["systemd-language-server"] = { "--version" },
}

local function cache_key(cmd, probe)
  if probe == nil or probe == false then
    return cmd .. "\0<none>"
  end
  return cmd .. "\0" .. table.concat(probe, "\0")
end

local function shell_join(argv)
  local escaped = {}
  for _, arg in ipairs(argv or {}) do
    table.insert(escaped, vim.fn.shellescape(arg))
  end
  return table.concat(escaped, " ")
end

M.shell_join = shell_join

local function run_probe(cmd, probe, timeout_ms)
  local argv = { cmd }
  vim.list_extend(argv, probe or {})

  if vim.system then
    local result = vim
      .system(argv, {
        text = true,
        timeout = timeout_ms or 2000,
      })
      :wait()
    return result.code == 0
  end

  vim.fn.system(shell_join(argv))
  return vim.v.shell_error == 0
end

function M.is_executable(cmd, opts)
  opts = opts or {}
  local predicate = opts.is_executable or function(bin)
    return vim.fn.executable(bin) == 1
  end
  return predicate(cmd) == true
end

function M.command_available(cmd, opts)
  opts = opts or {}
  if not M.is_executable(cmd, opts) then
    return false
  end

  local probe = opts.probe
  if probe == nil then
    probe = default_probes[cmd]
  end
  if probe == nil or probe == false then
    return true
  end

  local key = cache_key(cmd, probe)
  if cache[key] ~= nil then
    return cache[key]
  end

  local runner = opts.runner or run_probe
  local ok, available = pcall(runner, cmd, probe, opts.timeout_ms)
  local result = ok and available == true
  cache[key] = result
  return result
end

function M.has_any(cmds, opts_by_cmd)
  if type(cmds) == "string" then
    cmds = { cmds }
  end

  for _, cmd in ipairs(cmds or {}) do
    local opts = opts_by_cmd and opts_by_cmd[cmd] or nil
    if M.command_available(cmd, opts) then
      return true, cmd
    end
  end

  return false, nil
end

return M
