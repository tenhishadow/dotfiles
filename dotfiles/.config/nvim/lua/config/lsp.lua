-- LSP server configuration, diagnostics and attach-time keymaps.

local M = {}

local executable = require("utils.executable")
local languages = require("config.languages")

local has_modern_lsp = vim.lsp and vim.lsp.config and vim.lsp.enable
local has_lspconfig, lspconfig = false, nil

if not has_modern_lsp then
  has_lspconfig, lspconfig = pcall(require, "lspconfig")
end

local function has_any(cmds)
  return executable.has_any(cmds)
end

local function dirname(path)
  if vim.fs and vim.fs.dirname then
    return vim.fs.dirname(path)
  end
  return vim.fn.fnamemodify(path, ":p:h")
end

local function buffer_dir(bufnr)
  local name = vim.api.nvim_buf_get_name(bufnr)
  if name == "" then
    return nil
  end
  return dirname(name)
end

local function make_capabilities()
  local capabilities = vim.lsp.protocol.make_client_capabilities()
  local ok_blink, blink = pcall(require, "blink.cmp")
  if ok_blink and blink.get_lsp_capabilities then
    return blink.get_lsp_capabilities(capabilities)
  end
  return capabilities
end

local function server_name(modern_name, legacy_name)
  if has_modern_lsp then
    return modern_name
  end
  return legacy_name or modern_name
end

local diagnostic_icons = {
  Error = "E",
  Warn = "W",
  Hint = "H",
  Info = "I",
}

local function setup_diagnostics()
  if not (vim.diagnostic and vim.diagnostic.config) then
    return
  end

  local sev = vim.diagnostic.severity
  vim.diagnostic.config({
    virtual_text = false,
    signs = {
      text = {
        [sev.ERROR] = diagnostic_icons.Error,
        [sev.WARN] = diagnostic_icons.Warn,
        [sev.HINT] = diagnostic_icons.Hint,
        [sev.INFO] = diagnostic_icons.Info,
      },
    },
    underline = true,
    update_in_insert = false,
    severity_sort = true,
    float = { border = "rounded", source = "always" },
  })
end

local function diagnostic_jump(count)
  if vim.diagnostic.jump then
    return function()
      vim.diagnostic.jump({ count = count, float = true })
    end
  end
  if count < 0 then
    return vim.diagnostic.goto_prev
  end
  return vim.diagnostic.goto_next
end

local inlay_hint_filetypes = {
  gopls = { go = true },
  lua_ls = { lua = true },
  pylsp = { python = true },
  pyright = { python = true },
  tsserver = {
    javascript = true,
    javascriptreact = true,
    typescript = true,
    typescriptreact = true,
  },
  ts_ls = {
    javascript = true,
    javascriptreact = true,
    typescript = true,
    typescriptreact = true,
  },
}

local function supports_inlay_hints(client, bufnr)
  if not (client.server_capabilities and client.server_capabilities.inlayHintProvider) then
    return false
  end
  local allowed = inlay_hint_filetypes[client.name]
  return allowed and allowed[vim.bo[bufnr].filetype] == true
end

local function enable_inlay_hints(client, bufnr)
  if not supports_inlay_hints(client, bufnr) then
    return
  end

  local inlay_hint = vim.lsp.inlay_hint
  if type(inlay_hint) == "table" and inlay_hint.enable then
    pcall(inlay_hint.enable, true, { bufnr = bufnr })
  elseif type(inlay_hint) == "function" then
    pcall(inlay_hint, bufnr, true)
  end
end

local function setup_attach()
  local group = vim.api.nvim_create_augroup("dotfiles_lsp_attach", { clear = true })

  vim.api.nvim_create_autocmd("LspAttach", {
    group = group,
    callback = function(args)
      local bufnr = args.buf
      local client = vim.lsp.get_client_by_id(args.data.client_id)

      local function map(mode, lhs, rhs, desc)
        vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true, desc = desc })
      end

      map("n", "gd", vim.lsp.buf.definition, "LSP: Go to Definition")
      map("n", "K", vim.lsp.buf.hover, "LSP: Hover")
      map("n", "gi", vim.lsp.buf.implementation, "LSP: Go to Implementation")
      map("n", "<leader>rn", vim.lsp.buf.rename, "LSP: Rename")
      map("n", "<leader>ca", vim.lsp.buf.code_action, "LSP: Code Action")
      map("n", "[d", diagnostic_jump(-1), "LSP: Prev Diagnostic")
      map("n", "]d", diagnostic_jump(1), "LSP: Next Diagnostic")
      map("n", "<leader>q", vim.diagnostic.setloclist, "LSP: Diagnostics to LocList")

      if client then
        enable_inlay_hints(client, bufnr)
      end
    end,
  })
end

local function configure(name, opts)
  opts = opts or {}

  if has_modern_lsp then
    vim.lsp.config(name, opts)
    vim.lsp.enable(name)
    return
  end

  if has_lspconfig and lspconfig[name] then
    lspconfig[name].setup(opts)
  end
end

local function add_schema_settings(configs)
  local ok_schemastore, schemastore = pcall(require, "schemastore")

  if configs.yamlls then
    configs.yamlls.settings = {
      redhat = { telemetry = { enabled = false } },
      yaml = {
        keyOrdering = false,
        format = { enable = true },
        validate = true,
        schemaStore = {
          enable = false,
          url = "",
        },
      },
    }

    if ok_schemastore then
      configs.yamlls.settings.yaml.schemas = schemastore.yaml.schemas()
    end
  end

  if configs.jsonls then
    configs.jsonls.settings = {
      json = {
        format = { enable = true },
        validate = { enable = true },
      },
    }

    if ok_schemastore then
      configs.jsonls.settings.json.schemas = schemastore.json.schemas()
    end
  end
end

local function build_server_configs(capabilities)
  local configs = {}

  if has_any(languages.lsp_bins.pyright) then
    configs.pyright = {}
  elseif has_any(languages.lsp_bins.pylsp) then
    configs.pylsp = {
      settings = {
        pylsp = {
          plugins = {
            black = { enabled = true },
            mccabe = { enabled = false },
            pycodestyle = { enabled = false },
            pyflakes = { enabled = false },
          },
        },
      },
    }
  end

  for _, server in ipairs({
    { name = "ansiblels" },
    { name = "bashls" },
    { name = "dockerls" },
    { name = "eslint" },
    { name = "gopls" },
    { name = "helm_ls" },
    { name = "jsonls" },
    { name = "lua_ls" },
    { name = "ruby_lsp" },
    { name = "terraformls" },
    { name = "ts_ls" },
    { name = "yamlls" },
  }) do
    if has_any(languages.lsp_bins[server.name]) then
      configs[server_name(server.name, server.legacy)] = configs[server.name] or {}
    end
  end

  if configs.lua_ls then
    configs.lua_ls.settings = {
      Lua = {
        diagnostics = {
          globals = { "vim" },
        },
        workspace = {
          checkThirdParty = false,
          library = {
            vim.env.VIMRUNTIME,
            vim.fn.stdpath("config"),
          },
        },
        telemetry = { enable = false },
      },
    }
  end

  local typescript_server = server_name("ts_ls", "tsserver")
  if configs[typescript_server] then
    configs[typescript_server].cmd = { "typescript-language-server", "--stdio" }
  end

  if has_any(languages.lsp_bins.systemd_lsp) then
    local root_dir
    if has_modern_lsp then
      root_dir = function(bufnr, on_dir)
        local root = buffer_dir(bufnr)
        if root then
          on_dir(root)
        end
      end
    else
      root_dir = dirname
    end

    configs[server_name("systemd_lsp", "systemd_ls")] = {
      cmd = { "systemd-language-server" },
      filetypes = { "systemd" },
      root_dir = root_dir,
    }
  end

  add_schema_settings(configs)

  for _, cfg in pairs(configs) do
    cfg.capabilities = capabilities
  end

  return configs
end

function M.setup()
  if not has_modern_lsp and not has_lspconfig then
    return
  end

  setup_diagnostics()
  setup_attach()

  local capabilities = make_capabilities()
  local configs = build_server_configs(capabilities)

  for server, config in pairs(configs) do
    configure(server, config)
  end
end

return M
