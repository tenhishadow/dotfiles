-- Canonical user-facing Neovim keymap inventory.
--
-- Keep all intentional user-facing keymaps here so runtime config,
-- generated documentation, and review checks stay aligned.

local M = {}

M.leader = {
  value = " ",
  label = "Space",
  notation = "<leader>",
}

M.localleader = {
  value = "\\",
  label = "\\",
  notation = "<localleader>",
}

M.which_key_groups = {
  { "<leader>c", group = "code" },
  { "<leader>f", group = "find" },
  { "<leader>h", group = "git hunk" },
  { "<leader>r", group = "rename" },
  { "<leader>t", group = "toggles" },
}

M.sections = {
  {
    name = "Core",
    maps = {
      {
        id = "toggle_paste",
        mode = "n",
        lhs = "<leader>tp",
        desc = "Editor: Toggle Paste Mode",
      },
    },
  },
  {
    name = "Find",
    maps = {
      {
        id = "files",
        mode = "n",
        lhs = "<leader>ff",
        rhs = ":Files<CR>",
        desc = "FZF: Files",
      },
      {
        id = "buffers",
        mode = "n",
        lhs = "<leader>fb",
        rhs = ":Buffers<CR>",
        desc = "FZF: Buffers",
      },
      {
        id = "git_files",
        mode = "n",
        lhs = "<leader>fg",
        rhs = ":GFiles<CR>",
        desc = "FZF: Git Files",
      },
      {
        id = "lines",
        mode = "n",
        lhs = "<leader>fl",
        rhs = ":Lines<CR>",
        desc = "FZF: Lines",
      },
    },
  },
  {
    name = "Explorer",
    maps = {
      {
        id = "reveal",
        mode = "n",
        lhs = "\\",
        rhs = ":Neotree reveal<CR>",
        desc = "NeoTree: Reveal Current File",
        silent = true,
      },
    },
  },
  {
    name = "Editing",
    maps = {
      {
        id = "easy_align",
        mode = { "n", "x" },
        lhs = "ga",
        rhs = "<Plug>(EasyAlign)",
        desc = "Format: Align Text",
        remap = true,
      },
    },
  },
  {
    name = "Git",
    maps = {
      {
        id = "next_change",
        mode = "n",
        lhs = "]c",
        desc = "Git: Next Change",
      },
      {
        id = "previous_change",
        mode = "n",
        lhs = "[c",
        desc = "Git: Previous Change",
      },
      {
        id = "stage_hunk_visual",
        mode = "v",
        lhs = "<leader>hs",
        desc = "Git: Stage Selected Hunk",
      },
      {
        id = "reset_hunk_visual",
        mode = "v",
        lhs = "<leader>hr",
        desc = "Git: Reset Selected Hunk",
      },
      {
        id = "stage_hunk",
        mode = "n",
        lhs = "<leader>hs",
        desc = "Git: Toggle Hunk Stage",
      },
      {
        id = "reset_hunk",
        mode = "n",
        lhs = "<leader>hr",
        desc = "Git: Reset Hunk",
      },
      {
        id = "stage_buffer",
        mode = "n",
        lhs = "<leader>hS",
        desc = "Git: Stage Buffer",
      },
      {
        id = "unstage_hunk",
        mode = "n",
        lhs = "<leader>hu",
        desc = "Git: Unstage Hunk",
      },
      {
        id = "reset_buffer",
        mode = "n",
        lhs = "<leader>hR",
        desc = "Git: Reset Buffer",
      },
      {
        id = "preview_hunk",
        mode = "n",
        lhs = "<leader>hp",
        desc = "Git: Preview Hunk",
      },
      {
        id = "blame_line",
        mode = "n",
        lhs = "<leader>hb",
        desc = "Git: Blame Line",
      },
      {
        id = "diff_index",
        mode = "n",
        lhs = "<leader>hd",
        desc = "Git: Diff Index",
      },
      {
        id = "diff_last_commit",
        mode = "n",
        lhs = "<leader>hD",
        desc = "Git: Diff Last Commit",
      },
      {
        id = "toggle_line_blame",
        mode = "n",
        lhs = "<leader>tb",
        desc = "Git: Toggle Line Blame",
      },
      {
        id = "show_deleted_inline",
        mode = "n",
        lhs = "<leader>tD",
        desc = "Git: Show Deleted Inline",
      },
    },
  },
  {
    name = "LSP",
    maps = {
      {
        id = "definition",
        mode = "n",
        lhs = "gd",
        desc = "LSP: Go to Definition",
      },
      {
        id = "hover",
        mode = "n",
        lhs = "K",
        desc = "LSP: Hover",
      },
      {
        id = "implementation",
        mode = "n",
        lhs = "gi",
        desc = "LSP: Go to Implementation",
      },
      {
        id = "rename",
        mode = "n",
        lhs = "<leader>rn",
        desc = "LSP: Rename",
      },
      {
        id = "code_action",
        mode = "n",
        lhs = "<leader>ca",
        desc = "LSP: Code Action",
      },
      {
        id = "previous_diagnostic",
        mode = "n",
        lhs = "[d",
        desc = "LSP: Previous Diagnostic",
      },
      {
        id = "next_diagnostic",
        mode = "n",
        lhs = "]d",
        desc = "LSP: Next Diagnostic",
      },
      {
        id = "diagnostics_loclist",
        mode = "n",
        lhs = "<leader>q",
        desc = "LSP: Diagnostics to LocList",
      },
    },
  },
  {
    name = "Debug",
    maps = {
      {
        id = "continue",
        mode = "n",
        lhs = "<F5>",
        desc = "Debug: Start or Continue",
      },
      {
        id = "step_into",
        mode = "n",
        lhs = "<F1>",
        desc = "Debug: Step Into",
      },
      {
        id = "step_over",
        mode = "n",
        lhs = "<F2>",
        desc = "Debug: Step Over",
      },
      {
        id = "step_out",
        mode = "n",
        lhs = "<F3>",
        desc = "Debug: Step Out",
      },
      {
        id = "toggle_breakpoint",
        mode = "n",
        lhs = "<leader>b",
        desc = "Debug: Toggle Breakpoint",
      },
      {
        id = "conditional_breakpoint",
        mode = "n",
        lhs = "<leader>B",
        desc = "Debug: Set Conditional Breakpoint",
      },
      {
        id = "toggle_ui",
        mode = "n",
        lhs = "<F7>",
        desc = "Debug: Toggle UI",
      },
    },
  },
}

for _, section in ipairs(M.sections) do
  M[section.name:lower()] = section.maps
end

function M.to_lazy_keys(maps)
  return vim.tbl_map(function(keymap)
    return {
      keymap.lhs,
      keymap.rhs,
      mode = keymap.mode,
      desc = keymap.desc,
      silent = keymap.silent,
      remap = keymap.remap,
    }
  end, maps)
end

return M
