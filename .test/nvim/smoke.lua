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

local function get_matching_client(bufnr, expected)
  local clients = get_clients(bufnr)
  if not expected or #expected == 0 then
    return clients[1]
  end
  for _, c in ipairs(clients) do
    for _, name in ipairs(expected) do
      if c.name == name then
        return c
      end
    end
  end
  return clients[1]
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
  return vim.wait(timeout_ms or 8000, has_client, 100)
end

local function pick_candidate(candidates)
  for _, cand in ipairs(candidates or {}) do
    if has_any(cand.binaries or {}) then
      return cand
    end
  end
  return nil
end

local function find_needle_position(bufnr, needle)
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
  for i, line in ipairs(lines) do
    local s = string.find(line, needle, 1, true)
    if s then
      return { line = i - 1, character = s - 1 }
    end
  end
  return nil
end

local function lsp_supports(client, method)
  if not client then
    return false
  end
  if client.supports_method then
    return client:supports_method(method)
  end
  local caps = client.server_capabilities or {}
  if method == "textDocument/hover" then
    return caps.hoverProvider
  end
  if method == "textDocument/definition" then
    return caps.definitionProvider
  end
  if method == "textDocument/documentSymbol" then
    return caps.documentSymbolProvider
  end
  return true
end

local function get_keymaps(bufnr, lhs)
  if vim.keymap and vim.keymap.get then
    return vim.keymap.get("n", lhs, { buffer = bufnr }) or {}
  end
  local maps = {}
  local ok, buf_maps = pcall(vim.api.nvim_buf_get_keymap, bufnr, "n")
  if not ok then
    return {}
  end
  for _, map in ipairs(buf_maps or {}) do
    if map.lhs == lhs then
      table.insert(maps, map)
    end
  end
  return maps
end

local function run_lsp_keymaps(bufnr, test_name)
  local mappings = {
    { lhs = "gd", desc = "LSP: Go to Definition" },
    { lhs = "K", desc = "LSP: Hover" },
    { lhs = "gi", desc = "LSP: Go to Implementation" },
    { lhs = "[d", desc = "LSP: Prev Diagnostic" },
    { lhs = "]d", desc = "LSP: Next Diagnostic" },
  }

  for _, km in ipairs(mappings) do
    local maps = get_keymaps(bufnr, km.lhs)
    local ok = false
    for _, map in ipairs(maps) do
      if map.desc == nil or map.desc == km.desc then
        ok = true
        break
      end
    end
    if not ok then
      add_error("Missing LSP keymap for " .. test_name .. ": " .. km.lhs)
    end
  end
end

local function run_lsp_request(bufnr, client, test)
  local req = test.lsp and test.lsp.request or nil
  if not req or not client then
    return
  end
  local method = req.method or "textDocument/hover"
  local function request_fail(reason)
    if req.required then
      add_error("LSP request " .. reason .. " for " .. test.name .. ": " .. method)
    else
      log("LSP: skip " .. test.name .. " (" .. reason .. ": " .. method .. ")")
    end
  end
  if not lsp_supports(client, method) then
    if req.required then
      add_error("LSP method not supported for " .. test.name .. ": " .. method)
    end
    return
  end
  local pos = req.position
  if not pos and req.needle then
    pos = find_needle_position(bufnr, req.needle)
  end
  if not pos then
    request_fail("position not found")
    return
  end
  local util = vim.lsp.util
  if not util or not util.make_position_params then
    request_fail("util unavailable")
    return
  end
  local enc = client.offset_encoding or "utf-16"
  local ok_params, params = pcall(util.make_position_params, 0, enc)
  if not ok_params then
    ok_params, params = pcall(util.make_position_params)
  end
  if not ok_params or type(params) ~= "table" then
    request_fail("position params failed")
    return
  end
  params.textDocument = util.make_text_document_params(bufnr)
  params.position = pos
  local resp = vim.lsp.buf_request_sync(bufnr, method, params, req.timeout_ms or 2000)
  if not resp then
    request_fail("timed out")
    return
  end
  local ok = false
  for _, r in pairs(resp) do
    if r and r.result ~= nil then
      ok = true
      break
    end
  end
  if not ok then
    request_fail("returned empty result")
  end
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
    return
  end
  run_lsp_keymaps(bufnr, test.name)
  local client = get_matching_client(bufnr, expected)
  run_lsp_request(bufnr, client, test)
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
    async = false,
  })
  if not ok then
    add_error("Formatter failed for " .. test.name .. ": " .. tostring(err))
  else
    vim.bo[bufnr].modified = false
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

local function run_treesitter(bufnr, test)
  if not test.treesitter then
    return
  end
  local strict = vim.fn.filereadable(vim.fn.stdpath("state") .. "/treesitter_install_ok") == 1
  local ts = test.treesitter
  local ok_parsers, parsers = pcall(require, "nvim-treesitter.parsers")
  if not ok_parsers then
    if strict then
      add_error("Treesitter not available for " .. test.name)
    else
      log("Treesitter: skip " .. test.name .. " (module missing)")
    end
    return
  end
  local ft
  if type(ts) == "table" then
    ft = ts.ft
  end
  if not ft or ft == "" then
    ft = vim.bo[bufnr].filetype
  end
  local lang
  if parsers.ft_to_lang then
    lang = parsers.ft_to_lang(ft)
  elseif parsers.get_buf_lang then
    lang = parsers.get_buf_lang(bufnr)
  end
  if not lang or lang == "" then
    lang = ft
  end
  if parsers.has_parser and not parsers.has_parser(lang) then
    if strict then
      add_error("Treesitter parser missing for " .. test.name .. " (" .. lang .. ")")
    else
      log("Treesitter: skip " .. test.name .. " (missing parser: " .. lang .. ")")
    end
    return
  end
  local ok_parser = pcall(vim.treesitter.get_parser, bufnr, lang)
  if not ok_parser then
    if strict then
      add_error("Treesitter parser failed for " .. test.name .. " (" .. lang .. ")")
    else
      log("Treesitter: skip " .. test.name .. " (parser failed: " .. lang .. ")")
    end
  end
end

local function run_plugin_checks()
  local ok_lazy, lazy = pcall(require, "lazy")
  if not ok_lazy then
    add_error("Lazy not available")
    return
  end

  local mason_utils = safe_require("utils.mason")
  local mason_mode = mason_utils and mason_utils.resolve_mode() or "off"

  local plugin_cmds = {
    { plugin = "neo-tree.nvim", cmds = { "Neotree" } },
    { plugin = "gitsigns.nvim", cmds = { "Gitsigns" } },
    { plugin = "which-key.nvim", cmds = { "WhichKey" } },
    { plugin = "undotree", cmds = { "UndotreeToggle" } },
    { plugin = "fzf.vim", cmds = { "Files", "Rg", "Buffers" } },
    { plugin = "vimwiki", cmds = { "VimwikiIndex" } },
    { plugin = "conform.nvim", cmds = { "ConformInfo" } },
    { plugin = "mason.nvim", cmds = mason_mode ~= "off" and { "Mason" } or {} },
    { plugin = "nvim-treesitter", cmds = {} },
  }

  local names = {}
  for _, item in ipairs(plugin_cmds) do
    table.insert(names, item.plugin)
  end
  pcall(lazy.load, { plugins = names })

  local function has_command(cmd)
    return vim.fn.exists(":" .. cmd) > 0
  end

  for _, item in ipairs(plugin_cmds) do
    for _, cmd in ipairs(item.cmds or {}) do
      if not has_command(cmd) then
        add_error("Missing command: " .. cmd .. " (plugin: " .. item.plugin .. ")")
      end
    end
  end

  local modules = { "conform", "lint", "gitsigns" }
  for _, mod in ipairs(modules) do
    if not safe_require(mod) then
      add_error("Missing module: " .. mod)
    end
  end

  if not vim.g.mkdp_filetypes or vim.g.mkdp_filetypes == "" then
    add_error("Missing markdown-preview config (mkdp_filetypes)")
  end

  local stats = lazy.stats and lazy.stats() or nil
  if not stats or not stats.count or stats.count == 0 then
    add_error("Lazy stats unavailable")
  end
end

local function run_mason_utils_tests()
  local mason_utils = safe_require("utils.mason")
  if not mason_utils then
    return
  end

  if mason_utils.resolve_mode("auto") ~= "auto" then
    add_error("Mason mode parse failed for auto")
  end
  if mason_utils.resolve_mode("1") ~= "always" then
    add_error("Mason mode parse failed for always")
  end
  if mason_utils.resolve_mode("") ~= "off" then
    add_error("Mason mode parse failed for off")
  end

  local missing = mason_utils.filter_missing(
    { "present", "absent" },
    { present = "present", absent = "absent" },
    function(cmd)
      return cmd == "present"
    end
  )
  if #missing ~= 1 or missing[1] ~= "absent" then
    add_error("Mason missing filter failed")
  end

  local missing_alias = mason_utils.filter_missing(
    { "alias" },
    { alias = { "bin-a", "bin-b" } },
    function(cmd)
      return cmd == "bin-b"
    end
  )
  if #missing_alias ~= 0 then
    add_error("Mason missing filter failed for aliases")
  end
end

run_mason_utils_tests()
run_plugin_checks()

local tests = {
  {
    name = "lua",
    path = "init.lua",
    ft = "lua",
    treesitter = true,
    root_files = { ".luarc.json" },
    lsp = {
      candidates = {
        { servers = { "lua_ls" }, binaries = { "lua-language-server" } },
      },
      request = {
        method = "textDocument/hover",
        needle = "foo",
        required = true,
      },
    },
  },
  {
    name = "python",
    path = "main.py",
    ft = "python",
    treesitter = true,
    root_files = { "pyproject.toml" },
    lsp = {
      candidates = {
        { servers = { "pyright" }, binaries = { "pyright-langserver", "pyright" } },
        { servers = { "pylsp" }, binaries = { "pylsp" } },
      },
      request = {
        method = "textDocument/hover",
        needle = "foo",
        required = true,
      },
    },
  },
  {
    name = "bash",
    path = "test.sh",
    ft = { "sh", "bash" },
    treesitter = { ft = "bash" },
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
    treesitter = true,
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
    treesitter = true,
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
      request = {
        method = "textDocument/hover",
        needle = "foo",
        required = true,
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
      request = {
        method = "textDocument/hover",
        needle = "foo",
        required = false,
        timeout_ms = 5000,
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
  {
    name = "markdown",
    path = "README.md",
    ft = { "markdown", "vimwiki" },
    treesitter = { ft = "markdown" },
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
    run_treesitter(bufnr, test)
    run_format(bufnr, test)
    run_lint(bufnr, test)
    vim.bo[bufnr].modified = false
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
