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

        map("n", "]c", function()
          if vim.wo.diff then
            vim.cmd.normal({ "]c", bang = true })
          else
            gitsigns.nav_hunk("next")
          end
        end, "Git: Next Change")

        map("n", "[c", function()
          if vim.wo.diff then
            vim.cmd.normal({ "[c", bang = true })
          else
            gitsigns.nav_hunk("prev")
          end
        end, "Git: Previous Change")

        map("v", "<leader>hs", function()
          gitsigns.stage_hunk({ vim.fn.line("."), vim.fn.line("v") })
        end, "Git: Stage Hunk")
        map("v", "<leader>hr", function()
          gitsigns.reset_hunk({ vim.fn.line("."), vim.fn.line("v") })
        end, "Git: Reset Hunk")
        map("n", "<leader>hs", gitsigns.stage_hunk, "Git: Stage Hunk")
        map("n", "<leader>hr", gitsigns.reset_hunk, "Git: Reset Hunk")
        map("n", "<leader>hS", gitsigns.stage_buffer, "Git: Stage Buffer")
        map("n", "<leader>hu", gitsigns.stage_hunk, "Git: Undo Stage Hunk")
        map("n", "<leader>hR", gitsigns.reset_buffer, "Git: Reset Buffer")
        map("n", "<leader>hp", gitsigns.preview_hunk, "Git: Preview Hunk")
        map("n", "<leader>hb", gitsigns.blame_line, "Git: Blame Line")
        map("n", "<leader>hd", gitsigns.diffthis, "Git: Diff Index")
        map("n", "<leader>hD", function()
          gitsigns.diffthis("@")
        end, "Git: Diff Last Commit")
        map("n", "<leader>tb", gitsigns.toggle_current_line_blame, "Git: Toggle Line Blame")
        map("n", "<leader>tD", gitsigns.preview_hunk_inline, "Git: Show Deleted Inline")
      end,
    },
  },
}
