if vim.fn.has("nvim-0.10") == 0 then
  return {}
end

local mason_utils = require("utils.mason")
local mason_mode = mason_utils.resolve_mode()

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
    keys = {
      {
        "<F5>",
        function()
          require("dap").continue()
        end,
        desc = "Debug: Start or Continue",
      },
      {
        "<F1>",
        function()
          require("dap").step_into()
        end,
        desc = "Debug: Step Into",
      },
      {
        "<F2>",
        function()
          require("dap").step_over()
        end,
        desc = "Debug: Step Over",
      },
      {
        "<F3>",
        function()
          require("dap").step_out()
        end,
        desc = "Debug: Step Out",
      },
      {
        "<leader>b",
        function()
          require("dap").toggle_breakpoint()
        end,
        desc = "Debug: Toggle Breakpoint",
      },
      {
        "<leader>B",
        function()
          require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: "))
        end,
        desc = "Debug: Set Conditional Breakpoint",
      },
      {
        "<F7>",
        function()
          require("dapui").toggle()
        end,
        desc = "Debug: Toggle UI",
      },
    },
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
