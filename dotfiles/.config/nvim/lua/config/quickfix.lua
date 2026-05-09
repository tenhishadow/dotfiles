-- Manual validation commands that send tool output to the quickfix list.

local M = {}

if not vim.api.nvim_create_user_command then
  return M
end

local executable = require("utils.executable")

local log_levels = (vim.log and vim.log.levels) or { INFO = "INFO", WARN = "WARN" }

local function notify(message, level)
  if vim.notify then
    vim.notify(message, level)
  else
    vim.api.nvim_echo({ { message } }, true, {})
  end
end

local function trim(value)
  return tostring(value or ""):gsub("^%s+", ""):gsub("%s+$", "")
end

local function split_lines(value)
  local lines = {}
  for line in (tostring(value or "") .. "\n"):gmatch("(.-)\n") do
    if line ~= "" then
      table.insert(lines, line)
    end
  end
  return lines
end

local function path_join(left, right)
  if left == "" then
    return right
  end
  return left:gsub("/+$", "") .. "/" .. right:gsub("^/+", "")
end

local function is_absolute(path)
  return path:match("^/") or path:match("^%a:[/\\]")
end

local function normalize_target(target)
  target = trim(target)
  if target ~= "" then
    return vim.fn.fnamemodify(target, ":p")
  end

  local file = vim.api.nvim_buf_get_name(0)
  if file ~= "" and vim.fn.filereadable(file) == 1 then
    return file
  end
  return vim.fn.getcwd()
end

local function nearest_dir_with(markers, start)
  local dir = start or vim.api.nvim_buf_get_name(0)
  if dir == "" then
    dir = vim.fn.getcwd()
  elseif vim.fn.filereadable(dir) == 1 then
    dir = vim.fn.fnamemodify(dir, ":p:h")
  else
    dir = vim.fn.fnamemodify(dir, ":p")
  end

  while dir and dir ~= "" do
    for _, marker in ipairs(markers) do
      local candidate = path_join(dir, marker)
      if marker:find("*", 1, true) and vim.fn.glob(candidate) ~= "" then
        return dir
      end
      if vim.fn.filereadable(candidate) == 1 or vim.fn.isdirectory(candidate) == 1 then
        return dir
      end
    end

    local parent = vim.fn.fnamemodify(dir, ":h")
    if parent == dir then
      break
    end
    dir = parent
  end

  return vim.fn.getcwd()
end

local function output_lines(result)
  if type(result) == "table" then
    local text = table.concat({ result.stdout or "", result.stderr or "" }, "\n")
    return split_lines(text)
  end
  return result or {}
end

local function run(argv, opts)
  opts = opts or {}
  local cwd = opts.cwd or vim.fn.getcwd()

  if not executable.is_executable(argv[1]) then
    notify("Missing executable: " .. argv[1], log_levels.WARN)
    return
  end

  local code = 0
  local lines = {}
  if vim.system then
    local result = vim.system(argv, { cwd = cwd, text = true }):wait()
    code = result.code or 0
    lines = output_lines(result)
  else
    lines = vim.fn.systemlist("cd " .. vim.fn.shellescape(cwd) .. " && " .. executable.shell_join(argv))
    code = vim.v.shell_error
  end

  local items = {}
  for _, line in ipairs(lines) do
    local file, lnum, col, text = line:match("^([^:%s][^:]*):(%d+):(%d+):%s*(.*)$")
    if file then
      if not is_absolute(file) then
        file = path_join(cwd, file)
      end
      table.insert(items, {
        filename = file,
        lnum = tonumber(lnum),
        col = tonumber(col),
        text = text,
      })
    else
      file, lnum, text = line:match("^([^:%s][^:]*):(%d+):%s*(.*)$")
      if file then
        if not is_absolute(file) then
          file = path_join(cwd, file)
        end
        table.insert(items, {
          filename = file,
          lnum = tonumber(lnum),
          text = text,
        })
      else
        table.insert(items, { text = line })
      end
    end
  end

  if #items == 0 then
    table.insert(items, { text = opts.title .. ": no output" })
  end

  vim.fn.setqflist({}, "r", {
    title = opts.title or table.concat(argv, " "),
    items = items,
  })
  vim.cmd("copen")

  if code == 0 then
    notify((opts.title or argv[1]) .. " completed", log_levels.INFO)
  else
    notify((opts.title or argv[1]) .. " exited with code " .. code, log_levels.WARN)
  end
end

local function command(name, desc, callback)
  vim.api.nvim_create_user_command(name, callback, {
    nargs = "?",
    complete = "file",
    desc = desc,
  })
end

command("DotfilesKubeconform", "Validate Kubernetes YAML with kubeconform", function(opts)
  local target = normalize_target(opts.args)
  local argv = { "kubeconform", "-summary", "-strict", "-ignore-missing-schemas" }
  if vim.fn.isdirectory(target) == 1 then
    table.insert(argv, "-recursive")
  end
  table.insert(argv, target)
  run(argv, { title = "kubeconform", cwd = vim.fn.getcwd() })
end)

command("DotfilesHelmLint", "Run helm lint for a chart", function(opts)
  local target = trim(opts.args)
  if target == "" then
    target = nearest_dir_with({ "Chart.yaml", "Chart.yml" })
  end
  run({ "helm", "lint", target }, { title = "helm lint", cwd = vim.fn.getcwd() })
end)

command("DotfilesKustomizeBuild", "Run kustomize build", function(opts)
  local target = trim(opts.args)
  if target == "" then
    target = nearest_dir_with({ "kustomization.yaml", "kustomization.yml", "Kustomization" })
  end
  run({ "kustomize", "build", target }, { title = "kustomize build", cwd = vim.fn.getcwd() })
end)

command("DotfilesTerraformValidate", "Run terraform validate", function(opts)
  local target = trim(opts.args)
  if target == "" then
    target = nearest_dir_with({ ".terraform", "*.tf" })
  end
  run({ "terraform", "-chdir=" .. target, "validate", "-no-color" }, { title = "terraform validate", cwd = vim.fn.getcwd() })
end)

command("DotfilesTofuValidate", "Run tofu validate", function(opts)
  local target = trim(opts.args)
  if target == "" then
    target = nearest_dir_with({ ".terraform", "*.tofu", "*.tf" })
  end
  run({ "tofu", "-chdir=" .. target, "validate", "-no-color" }, { title = "tofu validate", cwd = vim.fn.getcwd() })
end)

command("DotfilesTrivyConfig", "Scan configuration with trivy", function(opts)
  local target = normalize_target(opts.args)
  run({ "trivy", "config", "--no-progress", target }, { title = "trivy config", cwd = vim.fn.getcwd() })
end)

command("DotfilesGitleaksDetect", "Scan repository secrets with gitleaks", function(opts)
  local target = normalize_target(opts.args)
  run({ "gitleaks", "detect", "--no-banner", "--redact", "--source", target }, {
    title = "gitleaks detect",
    cwd = vim.fn.getcwd(),
  })
end)

command("DotfilesSemgrep", "Scan code with semgrep", function(opts)
  local target = normalize_target(opts.args)
  run({ "semgrep", "scan", "--quiet", target }, { title = "semgrep", cwd = vim.fn.getcwd() })
end)

return M
