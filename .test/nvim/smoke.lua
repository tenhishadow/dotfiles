-- Headless smoke tests for Neovim config.

vim.o.swapfile = false

local function log(msg)
  vim.api.nvim_echo({ { msg } }, true, {})
end

local errors = {}

local function add_error(msg)
  table.insert(errors, msg)
end

local function safe_require(name)
  local ok, mod = pcall(require, name)
  if ok then
    return mod
  end
  return nil
end

local function has_exe(cmd)
  return vim.fn.executable(cmd) == 1
end

local function has_any(cmds)
  for _, cmd in ipairs(cmds or {}) do
    if has_exe(cmd) then
      return true
    end
  end
  return false
end

local base_root = vim.fn.getcwd() .. "/.test/nvim"

local function fixture_path(spec)
  local root = base_root .. "/" .. spec.name
  local file_path = root .. "/" .. spec.path
  return root, file_path
end

local function path_exists(path)
  return vim.fn.isdirectory(path) == 1 or vim.fn.filereadable(path) == 1
end

local function open_file(path)
  vim.cmd("edit " .. vim.fn.fnameescape(path))
  if vim.bo.filetype == "" then
    vim.cmd("filetype detect")
  end
  return vim.api.nvim_get_current_buf()
end

local function ft_label(expected)
  if type(expected) == "string" then
    return expected
  end
  return table.concat(expected, "|")
end

local function ft_matches(actual, expected)
  if type(expected) == "string" then
    return actual == expected
  end
  for _, ft in ipairs(expected) do
    if actual == ft then
      return true
    end
  end
  return false
end

local function get_clients(bufnr)
  if not vim.lsp then
    return {}
  end
  if vim.lsp.get_clients then
    return vim.lsp.get_clients({ bufnr = bufnr })
  end
  return vim.lsp.get_active_clients({ bufnr = bufnr })
end

local function wait_for_lsp(bufnr, expected, timeout_ms)
  if not vim.lsp then
    return false
  end
  local function has_client()
    local clients = get_clients(bufnr)
    if not expected or #expected == 0 then
      return #clients > 0
    end
    for _, c in ipairs(clients) do
      for _, name in ipairs(expected) do
        if c.name == name then
          return true
        end
      end
    end
    return false
  end
  return vim.wait(timeout_ms or 5000, has_client, 100)
end

local function pick_candidate(candidates)
  for _, cand in ipairs(candidates or {}) do
    if has_any(cand.binaries or {}) then
      return cand
    end
  end
  return nil
end

local function run_lsp(test, bufnr)
  if not test.lsp or not test.lsp.candidates then
    return
  end
  local cand = pick_candidate(test.lsp.candidates)
  if not cand then
    log("LSP: skip " .. test.name .. " (no binaries)")
    return
  end
  local expected = cand.servers or {}
  if not wait_for_lsp(bufnr, expected, test.lsp.timeout_ms) then
    local label = #expected > 0 and table.concat(expected, "/") or "any"
    add_error("LSP not attached for " .. test.name .. " (expected: " .. label .. ")")
  end
end

local function run_format(bufnr, test)
  local conform = safe_require("conform")
  if not conform or type(conform.list_formatters) ~= "function" then
    return
  end
  local formatters = conform.list_formatters(bufnr)
  if not formatters or #formatters == 0 then
    return
  end
  local has_available = false
  for _, f in ipairs(formatters) do
    if f.available then
      has_available = true
      break
    end
  end
  if not has_available then
    log("Format: skip " .. test.name .. " (no available formatter)")
    return
  end
  local ok, err = pcall(conform.format, {
    bufnr = bufnr,
    timeout_ms = 2000,
    lsp_format = "never",
  })
  if not ok then
    add_error("Formatter failed for " .. test.name .. ": " .. tostring(err))
  end
end

local function run_lint(bufnr, test)
  local lint = safe_require("lint")
  if not lint or type(lint.try_lint) ~= "function" then
    return
  end
  local ft = vim.bo[bufnr].filetype
  local linters = lint.linters_by_ft and lint.linters_by_ft[ft] or nil
  if not linters or #linters == 0 then
    return
  end
  local ok, err = pcall(lint.try_lint)
  if not ok then
    add_error("Lint failed for " .. test.name .. ": " .. tostring(err))
  end
end

local tests = {
  {
    name = "lua",
    path = "init.lua",
    ft = "lua",
    root_files = { ".luarc.json" },
    lsp = {
      candidates = {
        { servers = { "lua_ls" }, binaries = { "lua-language-server" } },
      },
    },
  },
  {
    name = "python",
    path = "main.py",
    ft = "python",
    root_files = { "pyproject.toml" },
    lsp = {
      candidates = {
        { servers = { "pyright" }, binaries = { "pyright-langserver", "pyright" } },
        { servers = { "pylsp" }, binaries = { "pylsp" } },
      },
    },
  },
  {
    name = "bash",
    path = "test.sh",
    ft = { "sh", "bash" },
    lsp = {
      candidates = {
        { servers = { "bashls" }, binaries = { "bash-language-server" } },
      },
    },
  },
  {
    name = "yaml",
    path = "config.yaml",
    ft = "yaml",
    lsp = {
      candidates = {
        { servers = { "yamlls" }, binaries = { "yaml-language-server" } },
      },
    },
  },
  {
    name = "ansible",
    path = "playbook.yml",
    ft = "yaml.ansible",
    lsp = {
      candidates = {
        { servers = { "ansiblels" }, binaries = { "ansible-language-server" } },
      },
    },
  },
  {
    name = "json",
    path = "data.json",
    ft = "json",
    lsp = {
      candidates = {
        {
          servers = { "jsonls" },
          binaries = {
            "vscode-json-language-server",
            "vscode-json-languageserver",
            "vscode-json-language-server-cli",
          },
        },
      },
    },
  },
  {
    name = "terraform",
    path = "main.tf",
    ft = "terraform",
    root_files = { ".terraform" },
    lsp = {
      candidates = {
        { servers = { "terraformls" }, binaries = { "terraform-ls" } },
      },
    },
  },
  {
    name = "terragrunt",
    path = "terragrunt.hcl",
    ft = "terraform",
    root_files = { ".terraform" },
    lsp = {
      candidates = {
        { servers = { "terraformls" }, binaries = { "terraform-ls" } },
      },
    },
  },
  {
    name = "go",
    path = "main.go",
    ft = "go",
    root_files = { "go.mod" },
    lsp = {
      candidates = {
        { servers = { "gopls" }, binaries = { "gopls" } },
      },
    },
  },
  {
    name = "typescript",
    path = "main.ts",
    ft = "typescript",
    root_files = { "package.json" },
    lsp = {
      candidates = {
        { servers = { "ts_ls", "tsserver" }, binaries = { "typescript-language-server" } },
      },
    },
  },
  {
    name = "dockerfile",
    path = "Dockerfile",
    ft = "dockerfile",
    lsp = {
      candidates = {
        { servers = { "dockerls" }, binaries = { "docker-langserver" } },
      },
    },
  },
  {
    name = "systemd",
    path = "smoke.service",
    ft = "systemd",
    lsp = {
      candidates = {
        { servers = { "systemd_lsp", "systemd_ls" }, binaries = { "systemd-language-server" } },
      },
    },
  },
  {
    name = "ruby",
    path = "main.rb",
    ft = "ruby",
    root_files = { "Gemfile" },
    lsp = {
      candidates = {
        { servers = { "ruby_lsp" }, binaries = { "ruby-lsp" } },
      },
    },
  },
}

for _, test in ipairs(tests) do
  log("Smoke: " .. test.name)
  local root, path = fixture_path(test)
  local ok_fixture = true
  if vim.fn.isdirectory(root) == 0 then
    add_error("Missing fixture dir for " .. test.name .. ": " .. root)
    ok_fixture = false
  end
  if vim.fn.filereadable(path) == 0 then
    add_error("Missing fixture file for " .. test.name .. ": " .. path)
    ok_fixture = false
  end
  if test.root_files then
    for _, rf in ipairs(test.root_files) do
      local root_path = root .. "/" .. rf
      if not path_exists(root_path) then
        add_error("Missing root marker for " .. test.name .. ": " .. root_path)
        ok_fixture = false
      end
    end
  end
  if ok_fixture then
    local bufnr = open_file(path)
    local ft = vim.bo[bufnr].filetype
    if test.ft and not ft_matches(ft, test.ft) then
      add_error("Filetype mismatch for " .. test.name .. ": expected " .. ft_label(test.ft) .. ", got " .. ft)
    end
    run_lsp(test, bufnr)
    run_format(bufnr, test)
    run_lint(bufnr, test)
  end
end

if #errors > 0 then
  log("Smoke FAILED:")
  for _, msg in ipairs(errors) do
    log("  - " .. msg)
  end
  vim.cmd("cq")
else
  log("Smoke OK")
  vim.cmd("qa")
end
