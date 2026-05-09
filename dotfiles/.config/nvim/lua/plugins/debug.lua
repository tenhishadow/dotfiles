if vim.fn.has("nvim-0.10") == 0 then
  return {}
end

local keymaps = require("config.keymaps_spec")
local mason_utils = require("utils.mason")
local mason_mode = mason_utils.resolve_mode()

local function dap_keymap_actions()
  return {
    continue = function()
      require("dap").continue()
    end,
    step_into = function()
      require("dap").step_into()
    end,
    step_over = function()
      require("dap").step_over()
    end,
    step_out = function()
      require("dap").step_out()
    end,
    toggle_breakpoint = function()
      require("dap").toggle_breakpoint()
    end,
    conditional_breakpoint = function()
      require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: "))
    end,
    toggle_ui = function()
      require("dapui").toggle()
    end,
  }
end

local function dap_keymaps()
  local actions = dap_keymap_actions()

  return vim.tbl_map(function(keymap)
    local action = assert(actions[keymap.id], "Missing DAP keymap action: " .. keymap.id)
    return {
      keymap.lhs,
      action,
      mode = keymap.mode,
      desc = keymap.desc,
    }
  end, keymaps.debug)
end

return {
  {
    "mfussenegger/nvim-dap",
    dependencies = {
      "rcarriga/nvim-dap-ui",
      "nvim-neotest/nvim-nio",
      {
        "mason-org/mason.nvim",
        enabled = mason_mode ~= "off",
      },
      {
        "jay-babu/mason-nvim-dap.nvim",
        enabled = mason_mode ~= "off",
      },
      "leoluz/nvim-dap-go",
    },
    keys = dap_keymaps(),
    config = function()
      local dap = require("dap")
      local dapui = require("dapui")

      if mason_mode ~= "off" then
        local ensure_installed = { "delve" }
        if mason_mode == "auto" then
          ensure_installed = mason_utils.filter_missing(ensure_installed, { delve = { "dlv", "delve" } })
        end

        require("mason-nvim-dap").setup({
          automatic_installation = mason_mode == "always",
          ensure_installed = ensure_installed,
          handlers = {},
        })
      end

      dapui.setup({
        icons = { expanded = "v", collapsed = ">", current_frame = "*" },
        controls = {
          icons = {
            disconnect = "D",
            pause = "P",
            play = ">",
            run_last = ">>",
            step_back = "b",
            step_into = "i",
            step_out = "o",
            step_over = "n",
            terminate = "x",
          },
        },
      })

      dap.listeners.after.event_initialized.dapui_config = dapui.open
      dap.listeners.before.event_terminated.dapui_config = dapui.close
      dap.listeners.before.event_exited.dapui_config = dapui.close

      require("dap-go").setup({
        delve = {
          detached = vim.fn.has("win32") == 0,
        },
      })
    end,
  },
}
