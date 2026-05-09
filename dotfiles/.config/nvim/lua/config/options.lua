-- lua/config/options.lua
-- Core Neovim options and settings.

----------------------------------------------------------------------
-- Providers
----------------------------------------------------------------------
-- The config does not use remote Node.js, Perl, or Ruby plugins. Keep these
-- providers disabled to avoid startup probes and optional health noise.
vim.g.loaded_node_provider = 0
vim.g.loaded_perl_provider = 0
vim.g.loaded_ruby_provider = 0

----------------------------------------------------------------------
-- Undo directory
----------------------------------------------------------------------
local undodir = vim.fn.stdpath("data") .. "/undodir"
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir = undodir

----------------------------------------------------------------------
-- Ensure Mason binaries are on PATH (mode-aware)
----------------------------------------------------------------------
do
  local mason_utils = require("utils.mason")
  local mason_mode = mason_utils.resolve_mode()
  if mason_mode ~= "off" then
    local mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
    if vim.fn.isdirectory(mason_bin) == 1 then
      local path = vim.env.PATH or ""
      local sep = (vim.fn.has("win32") == 1) and ";" or ":"
      if not string.find(path, mason_bin, 1, true) then
        if mason_mode == "auto" then
          if path == "" then
            vim.env.PATH = mason_bin
          else
            vim.env.PATH = path .. sep .. mason_bin
          end
        else
          if path == "" then
            vim.env.PATH = mason_bin
          else
            vim.env.PATH = mason_bin .. sep .. path
          end
        end
      end
    end
  end
end

-- Basic options
----------------------------------------------------------------------
if vim.fn.executable("bash") == 1 then
  vim.opt.shell = "bash"
end

vim.opt.termguicolors = true
vim.opt.background = "dark"
vim.opt.number = true
vim.opt.relativenumber = false

-- Use the system clipboard when a provider is available, so yanks survive
-- across buffers, tabs and separate Neovim instances.
do
  local executable = require("utils.executable")
  local has_clipboard = executable.has_any({
    "wl-copy",
    "xclip",
    "xsel",
    "pbcopy",
    "clip.exe",
    "win32yank.exe",
  })
  if has_clipboard then
    vim.opt.clipboard = "unnamedplus"
  end
end

vim.opt.diffopt:append("iwhite")
