-- init.lua

local M = {}

-- ========= Undo dir =========
local undodir = vim.fn.stdpath('data') .. '/undodir'
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir  = undodir

-- ========= Leaders (ДОЛЖНЫ быть до lazy) =========
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- ========= Глобальные настройки, которые полезно дать ДО плагинов =========
vim.opt.shell = "bash"
vim.opt.termguicolors = true       -- один раз, до темы
vim.opt.background = "dark"
vim.g.mkdp_filetypes = { "markdown", "vimwiki" } -- для markdown-preview

-- ========= Bootstrap lazy.nvim =========
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local out = vim.fn.system({
    "git","clone","--filter=blob:none","--branch=stable",
    "https://github.com/folke/lazy.nvim.git", lazypath
  })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar(); os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

-- ========= Плагины через lazy.nvim (ОДИН setup) =========
require("lazy").setup({
  spec = {
    -- UI / theme
    { "morhetz/gruvbox", lazy = false, priority = 1000,
      init = function()
        -- тема применится после загрузки
        vim.cmd.colorscheme("gruvbox")
      end
    },
    { "tomasr/molokai", lazy = true },
    { "jacoborus/tender.vim", lazy = true },
    { "itchyny/lightline.vim", event = "VeryLazy" },

    -- базовые утилиты
    { "mbbill/undotree", cmd = { "UndotreeToggle", "UndotreeShow" } },
    { "junegunn/fzf", build = "./install --bin" },
    { "junegunn/fzf.vim", dependencies = { "junegunn/fzf" }, keys = {
        { "<leader>ff", ":Files<CR>",   desc = "FZF Files"   },
        { "<leader>fb", ":Buffers<CR>", desc = "FZF Buffers" },
        { "<leader>fg", ":GFiles<CR>",  desc = "FZF Git"     },
        { "<leader>fl", ":Lines<CR>",   desc = "FZF Lines"   },
      }
    },
    { "vimwiki/vimwiki", ft = { "vimwiki" } },
    { "nvim-lua/plenary.nvim", lazy = true },

    -- LSP + completion
    { "neovim/nvim-lspconfig", event = { "BufReadPre", "BufNewFile" } },
    { "hrsh7th/nvim-cmp", event = "InsertEnter", dependencies = {
        "hrsh7th/cmp-nvim-lsp",
        "hrsh7th/cmp-path",
        "L3MON4D3/LuaSnip",
        "saadparwaiz1/cmp_luasnip",
      },
      config = function()
        local cmp = require("cmp")
        local luasnip = require("luasnip")
        cmp.setup({
          snippet = { expand = function(args) luasnip.lsp_expand(args.body) end },
          mapping = cmp.mapping.preset.insert({
            ["<CR>"]     = cmp.mapping.confirm({ select = true }),
            ["<C-Space>"] = cmp.mapping.complete(),
          }),
          sources = {
            { name = "nvim_lsp" },
            { name = "path" },
            { name = "luasnip" },
          },
        })
      end
    },

    -- форматирование / визуальное
    { "editorconfig/editorconfig-vim", event = "VeryLazy" },
    { "junegunn/vim-easy-align", keys = { { "ga", "<Plug>(EasyAlign)", mode = { "n","x" } } } },
    { "nathanaelkane/vim-indent-guides", event = "BufReadPre" },
    { "ntpeters/vim-better-whitespace", event = "BufReadPre",
      init = function() vim.g.better_whitespace_enabled = 1 end
    },

    -- языковые
    { "dense-analysis/ale", event = "BufReadPre" },
    { "sheerun/vim-polyglot", event = "VeryLazy" },

    -- python
    { "plytophogy/vim-virtualenv", ft = { "python" } },

    -- markdown
    { "plasticboy/vim-markdown", ft = { "markdown" } },
    { "iamcco/markdown-preview.nvim",
      cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
      ft = { "markdown" },
      build = function() vim.fn["mkdp#util#install"]() end,
    },

    -- mikrotik
    { "zainin/vim-mikrotik", ft = { "rsc", "mikrotik" } },

    -- HashiCorp
    { "hashivim/vim-terraform",    ft = { "terraform", "tf", "tfvars" } },
    { "hashivim/vim-consul",       ft = { "hcl" } },
    { "hashivim/vim-nomadproject", ft = { "hcl" } },
    { "hashivim/vim-vagrant",      ft = { "ruby", "vagrantfile" } },
    { "hashivim/vim-vaultproject", ft = { "hcl" } },

    -- Ruby / nginx / CloudFormation
    { "vim-ruby/vim-ruby", ft = { "ruby" } },
    { "chr4/nginx.vim",    ft = { "nginx" } },
    { "speshak/vim-cfn",   ft = { "yaml", "json" } },
  },

  checker = { enabled = true },
  change_detection = { enabled = true, notify = false },
  install = { colorscheme = { "habamax" } },
})

-- ========= Остальные опции редактора =========
vim.cmd("syntax on")           -- можно и не нужно в neovim, но не мешает
vim.opt.smartindent = true
vim.opt.autoread = true
vim.opt.backspace = { "indent", "eol", "start" }
vim.opt.clipboard = "unnamedplus"
vim.opt.expandtab = true
vim.opt.history = 1000

-- В neovim вместо 'viminfo' используют 'shada'
vim.opt.shada = "'100,<500,s10,h"

vim.opt.hlsearch = true
vim.opt.ignorecase = true
vim.opt.incsearch = true
vim.opt.mouse = ""             -- полностью без мыши
vim.opt.number = true
vim.opt.redrawtime = 10000
vim.opt.ruler = true
vim.opt.shiftwidth = 2
vim.opt.showmatch = true
vim.opt.smartcase = true
vim.opt.smarttab = true
vim.opt.synmaxcol = 250
vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.wildmenu = true
vim.opt.wildmode = { "list:longest", "full" }
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.showmode = false

-- restore cursor
local restore_cursor_group = vim.api.nvim_create_augroup("RestoreCursorPosition", { clear = true })
vim.api.nvim_create_autocmd("BufReadPost", {
  group = restore_cursor_group,
  pattern = "*",
  callback = function()
    local last_line = vim.fn.line("'\"")
    if last_line >= 1 and last_line <= vim.fn.line("$") and not string.match(vim.bo.filetype, "commit") then
      vim.cmd("normal! g`\"")
    end
  end,
})

-- ignore space in diff
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end

-- keymaps
vim.keymap.set('n', '<F2>', ':set invpaste paste?<CR>', { silent = true })
vim.keymap.set('x', 'ga', '<Plug>(EasyAlign)', {})
vim.keymap.set('n', 'ga', '<Plug>(EasyAlign)', {})

return M
