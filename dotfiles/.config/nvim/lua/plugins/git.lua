local keymaps = require("config.keymaps_spec")

return {
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    opts = {
      on_attach = function(bufnr)
        local gitsigns = require("gitsigns")

        local function map(mode, lhs, rhs, desc)
          vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc })
        end

        local actions = {
          next_change = function()
            if vim.wo.diff then
              vim.cmd.normal({ "]c", bang = true })
            else
              gitsigns.nav_hunk("next")
            end
          end,
          previous_change = function()
            if vim.wo.diff then
              vim.cmd.normal({ "[c", bang = true })
            else
              gitsigns.nav_hunk("prev")
            end
          end,
          stage_hunk_visual = function()
            gitsigns.stage_hunk({ vim.fn.line("."), vim.fn.line("v") })
          end,
          reset_hunk_visual = function()
            gitsigns.reset_hunk({ vim.fn.line("."), vim.fn.line("v") })
          end,
          stage_hunk = gitsigns.stage_hunk,
          reset_hunk = gitsigns.reset_hunk,
          stage_buffer = gitsigns.stage_buffer,
          -- stage_hunk toggles staged signs; undo_stage_hunk is deprecated upstream.
          unstage_hunk = gitsigns.stage_hunk,
          reset_buffer = gitsigns.reset_buffer,
          preview_hunk = gitsigns.preview_hunk,
          blame_line = gitsigns.blame_line,
          diff_index = gitsigns.diffthis,
          diff_last_commit = function()
            gitsigns.diffthis("@")
          end,
          toggle_line_blame = gitsigns.toggle_current_line_blame,
          show_deleted_inline = gitsigns.preview_hunk_inline,
        }

        for _, keymap in ipairs(keymaps.git) do
          local action = assert(actions[keymap.id], "Missing Git keymap action: " .. keymap.id)
          map(keymap.mode, keymap.lhs, action, keymap.desc)
        end
      end,
    },
  },
}
