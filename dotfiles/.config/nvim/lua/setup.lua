local M = {}

-- undodir
local undodir = vim.fn.stdpath('data') .. '/undodir'
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir  = undodir

-- vim-plug install
-- local plug_path = vim.fn.stdpath('data') .. '/site/autoload/plug.vim'
-- if vim.fn.filereadable(plug_path) == 0 then
--   if vim.fn.executable('curl') == 0 then
--     vim.api.nvim_err_writeln('ERR: you have to install curl or first install vim-plug yourself!')
--     vim.cmd('q!')
--   else
--     vim.fn.system({
--       'curl',
--       '-fLo', plug_path,
--       '--create-dirs',
--       'https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
--     })
--     local group = vim.api.nvim_create_augroup("gr_install_and_reload", { clear = true })
--     vim.api.nvim_create_autocmd("VimEnter", {
--       group = group,
--       pattern = "*",
--       command = "PlugInstall --sync | source $MYVIMRC"
--     })
--   end
-- end

-----------------------------------------------------
-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

-- Make sure to setup `mapleader` and `maplocalleader` before
-- loading lazy.nvim so that mappings are correct.
-- This is also a good place to setup other settings (vim.opt)
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- Setup lazy.nvim
require("lazy").setup({
  spec = {
    -- import your plugins
    { import = "plugins" },
  },
  -- Configure any other settings here. See the documentation for more details.
  -- colorscheme that will be used when installing plugins.
  install = { colorscheme = { "habamax" } },
  -- automatically check for plugin updates
  checker = { enabled = true },
})
-----------------------------------------------------



-- install plugs
local plug_dir = vim.fn.stdpath('data') .. '/plugged'
vim.cmd([[
  call plug#begin(']] .. plug_dir .. [[')

  " basic
  Plug 'itchyny/lightline.vim'
  Plug 'mbbill/undotree'
  Plug 'junegunn/fzf.vim'
  Plug 'vimwiki/vimwiki'
  Plug 'nvim-lua/plenary.nvim'

  " lsp
  Plug 'neovim/nvim-lspconfig'
  Plug 'hrsh7th/nvim-cmp'
  Plug 'hrsh7th/cmp-nvim-lsp'
  Plug 'L3MON4D3/LuaSnip'
  Plug 'saadparwaiz1/cmp_luasnip'
  Plug 'hrsh7th/cmp-path'

  " format
  Plug 'editorconfig/editorconfig-vim'
  Plug 'junegunn/vim-easy-align'
  Plug 'nathanaelkane/vim-indent-guides'
  Plug 'ntpeters/vim-better-whitespace'

  " theme
  Plug 'tomasr/molokai'
  Plug 'jacoborus/tender.vim'
  Plug 'morhetz/gruvbox'

  " language
  Plug 'dense-analysis/ale'
  Plug 'sheerun/vim-polyglot'

  " python
  Plug 'plytophogy/vim-virtualenv'

  " markdown
  Plug 'tpope/vim-markdown'
  Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }, 'for': ['markdown', 'vim-plug'] }

  " mikrotik
  Plug 'zainin/vim-mikrotik'

  " hashicorp
  Plug 'hashivim/vim-terraform'
  Plug 'hashivim/vim-consul'
  Plug 'hashivim/vim-nomadproject'
  Plug 'hashivim/vim-vagrant'
  Plug 'hashivim/vim-vaultproject'

  " ruby
  Plug 'vim-ruby/vim-ruby'

  " nginx
  Plug 'chr4/nginx.vim'

  " CloudFormation
  Plug 'speshak/vim-cfn'

  call plug#end()
]])

-- configure theme
local gruvbox_path = plug_dir .. '/gruvbox/colors/gruvbox.vim'
if vim.fn.filereadable(gruvbox_path) == 1 then
  vim.cmd("syntax enable")
  vim.cmd("colorscheme gruvbox")
  if vim.fn.has("termguicolors") == 1 then
    vim.opt.termguicolors = true
  end
  vim.opt.background = "dark"
  vim.g.lightline = { colorscheme = "gruvbox" }
  vim.g.gruvbox_guisp_fallback = "bg"
else
  local group = vim.api.nvim_create_augroup("gr_source", { clear = true })
  vim.api.nvim_create_autocmd("VimEnter", {
    group = group,
    pattern = "*",
    command = "PlugInstall --sync | source $MYVIMRC",
  })

  -- Выбираем запасную схему
  vim.cmd("colorscheme koehler")
  vim.g.lightline = { colorscheme = "koehler" }
end

vim.opt.shell = "bash"
vim.cmd("syntax on")


-- restore cursor
local restore_cursor_group = vim.api.nvim_create_augroup("RestoreCursorPosition", { clear = true })
vim.api.nvim_create_autocmd("BufReadPost", {
  group = restore_cursor_group,
  pattern = "*",
  callback = function()
    local last_line = vim.fn.line("'\"")
    if last_line >= 1
       and last_line <= vim.fn.line("$")
       and not string.match(vim.bo.filetype, "commit")
    then
      vim.cmd("normal! g`\"")
    end
  end,
})

-- ignore space in diff
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end

-- Автоматический отступ при создании новой строки.
vim.opt.smartindent = true
-- Автоматически перезагружать файл, если он был изменён снаружи.
-- (В Neovim это работает несколько иначе, но настройка всё ещё полезна.)
vim.opt.autoread = true
vim.opt.backspace = { "indent", "eol", "start" }
-- 5. clipboard
-- "unnamedplus" позволяет использовать системный буфер обмена.
vim.opt.clipboard = "unnamedplus"

-- 6. expandtab
-- Заменять символ табуляции на пробелы.
vim.opt.expandtab = true

-- 7. history
-- Устанавливаем размер истории команд.
vim.opt.history = 1000

-- 8. viminfo
-- Данные о сеансах и т.д. (в Neovim тоже работает, хотя формат может отличаться).
vim.opt.viminfo = "'100,<500,s10,h"

-- 9. hlsearch
-- Подсвечивать все вхождения найденного текста.
vim.opt.hlsearch = true

-- 10. ignorecase
-- Игнорировать регистр при поиске...
vim.opt.ignorecase = true

-- 11. incsearch
-- Показывать результаты поиска по мере ввода.
vim.opt.incsearch = true

-- zaebala
vim.opt.mouse = ""

-- 14. number
-- Включить нумерацию строк.
vim.opt.number = true

-- 15. redrawtime
-- Время, после которого Neovim "считаeт", что отрисовка слишком долгая.
-- В большинстве случаев нет смысла менять. Если нужно, оставляем:
vim.opt.redrawtime = 10000

-- 16. ruler
-- Показывать строку и столбец курсора в статус-строке.
-- Обычно плагины или встроенный статус-бар в Neovim делают это автоматически.
-- Но если хотите явно:
vim.opt.ruler = true

-- 17. shiftwidth
-- Шаг автоматического отступа.
vim.opt.shiftwidth = 2

-- 18. showmatch
-- Подсветка парных скобок.
vim.opt.showmatch = true

-- 19. smartcase
-- Включать чувствительность к регистру, если в поисковом запросе есть заглавные буквы.
vim.opt.smartcase = true

-- (Повторные set smartindent удалены; достаточно один раз.)

-- 20. smarttab
-- При использовании табуляций (при нажатии <Tab> на пустой строке) учитывает shiftwidth.
-- В Neovim это, как правило, включается автоматически вместе с expandtab/smartindent,
-- но можно явно включить:
vim.opt.smarttab = true

-- 21. synmaxcol
-- Обрезать синтаксическую подсветку до указанного столбца (для производительности).
vim.opt.synmaxcol = 250

-- 22. tabstop, softtabstop
-- Количество пробелов, соответствующее табу при редактировании.
vim.opt.tabstop = 2
vim.opt.softtabstop = 2

-- 23. termguicolors
-- Включает 24-битный цвет (TrueColor) в Neovim — рекомендуется.
vim.opt.termguicolors = true

-- 24. wildmenu, wildmode
-- Для удобного автодополнения в командной строке.
vim.opt.wildmenu = true
vim.opt.wildmode = { "list:longest", "full" }

-- ================================================
--   Настройки undo и файлов
-- ================================================

-- 1. noswapfile / nobackup
-- Отключение swap и backup. На усмотрение — если хотите минимизировать лишние файлы.
vim.opt.swapfile = false
vim.opt.backup = false

-- 3. showmode
-- Показывать внизу в каком вы режиме (INSERT, NORMAL, и т.д.).
-- Многие статус-лайны (например lualine, airline и т.п.) уже показывают режим.
-- Часто отключают showmode, чтобы не дублировать информацию.
vim.opt.showmode = false  -- можно включить true, если не используете статус-лайны

-- ================================================
--   Лидер клавиша
-- ================================================
-- Для Neovim в Lua:
vim.g.mapleader = ' '
-- Если нужно, чтобы она сработала до плагинов, разместите до их загрузки.

vim.keymap.set('n', '<F2>', ':set invpaste paste?<CR>', { silent = true })

-- ================================================
--   Пример для EasyAlign (если используется плагин)
-- ================================================
-- Плагины для Neovim обычно настраивают через любой менеджер плагинов (packer, lazy и т.д.).
-- Пример keymap:
-- Только учтите, что "<Plug>(EasyAlign)" – это "vimscript"-стиль.
-- В Lua можно делать то же самое, но сам плагин EasyAlign (если это https://github.com/junegunn/vim-easy-align)
-- всё равно использует те же маппинги.
-- Вы можете сохранить их так же:
vim.keymap.set('x', 'ga', '<Plug>(EasyAlign)', {})
vim.keymap.set('n', 'ga', '<Plug>(EasyAlign)', {})

vim.g.mkdp_filetypes = { 'markdown', 'vimwiki' }

return M

