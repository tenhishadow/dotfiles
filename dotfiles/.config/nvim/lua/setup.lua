-- Проверяем, установлен ли vim-plug
local plug_path = vim.fn.stdpath('data') .. '/site/autoload/plug.vim'
if vim.fn.filereadable(plug_path) == 0 then
  -- Если нет curl — выводим ошибку и выходим из Neovim
  if vim.fn.executable('curl') == 0 then
    vim.api.nvim_err_writeln('ERR: you have to install curl or first install vim-plug yourself!')
    vim.cmd('q!')
  else
    -- Скачиваем vim-plug
    vim.fn.system({
      'curl',
      '-fLo', plug_path,
      '--create-dirs',
      'https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
    })
    -- Создаём автокоманду, чтобы после запуска Neovim сразу выполнить PlugInstall и перезагрузить конфиг
    local group = vim.api.nvim_create_augroup("gr_install_and_reload", { clear = true })
    vim.api.nvim_create_autocmd("VimEnter", {
      group = group,
      pattern = "*",
      command = "PlugInstall --sync | source $MYVIMRC"
    })
  end
end

-- undodir
local undodir = vim.fn.stdpath('data') .. '/undodir'
if vim.fn.isdirectory(undodir) == 0 then
  vim.fn.mkdir(undodir, "p")
end
vim.opt.undofile = true
vim.opt.undodir  = undodir


-- Перед блоком plug#begin(), определим куда складывать плагины:
local plug_dir = vim.fn.stdpath('data') .. '/plugged'

-- Подключаем все плагины:
vim.cmd([[
  call plug#begin(']] .. plug_dir .. [[')

  " basic
  Plug 'itchyny/lightline.vim'
  Plug 'mbbill/undotree'
  Plug 'junegunn/fzf.vim'
  Plug 'vimwiki/vimwiki'

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
  Plug 'hashivim/vim-consul'
  Plug 'hashivim/vim-nomadproject'
  Plug 'hashivim/vim-packer'
  Plug 'hashivim/vim-terraform'
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

local gruvbox_path = plug_dir .. '/gruvbox/colors/gruvbox.vim'

-- Проверяем, установлена ли тема gruvbox
if vim.fn.filereadable(gruvbox_path) == 1 then
  -- Включаем gruvbox
  vim.cmd("syntax enable")
  vim.cmd("colorscheme gruvbox")

  -- Если Neovim поддерживает termguicolors, включаем
  if vim.fn.has("termguicolors") == 1 then
    vim.opt.termguicolors = true
  end

  -- Устанавливаем тёмную тему
  vim.opt.background = "dark"

  -- Настраиваем Lightline
  vim.g.lightline = { colorscheme = "gruvbox" }

  -- Дополнительно для gruvbox (если нужно)
  vim.g.gruvbox_guisp_fallback = "bg"
else
  -- Если gruvbox не установлен, устанавливаем плагины автоматически
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

-- folding
vim.opt.foldmethod = "syntax"
vim.opt.foldlevelstart = 1
-- folding params
vim.g.javaScript_fold     = 1
vim.g.perl_fold           = 1
vim.g.ruby_fold           = 1
vim.g.sh_fold_enabled     = 1
vim.g.vimsyn_folding      = "af"
vim.g.xml_syntax_folding  = 1

-- 1. Восстановить позицию курсора после открытия файла
local restore_cursor_group = vim.api.nvim_create_augroup("RestoreCursorPosition", { clear = true })
vim.api.nvim_create_autocmd("BufReadPost", {
  group = restore_cursor_group,
  pattern = "*",
  callback = function()
    -- Аналог Vimscript:
    -- if line("'\"") >= 1 && line("'\"") <= line("$") && &filetype !~# 'commit'
    local last_line = vim.fn.line("'\"")
    if last_line >= 1
       and last_line <= vim.fn.line("$")
       and not string.match(vim.bo.filetype, "commit")
    then
      vim.cmd("normal! g`\"")
    end
  end,
})

-- 2. Для файлов YAML устанавливаем foldmethod=marker и foldlevel=0
local custom_folds_group = vim.api.nvim_create_augroup("custom_folds", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = custom_folds_group,
  pattern = "yaml",
  callback = function()
    vim.opt_local.foldmethod = "marker"
    vim.opt_local.foldlevel = 0
  end,
})

-- 3. Игнорирование пробелов в режиме diff
-- Если Neovim запущен с опцией --diff или включен diff-режим, то делаем diffopt += iwhite
if vim.opt.diff:get() then
  vim.opt.diffopt:append("iwhite")
end

-- ================================================
--   Общие настройки (опции Neovim)
-- ================================================

-- 1. Комментарии курсивом
-- По умолчанию цветовая схема может переопределить стиль для группы 'Comment'.
-- Если хотите гарантированно курсив, можно задать так (работает в Neovim 0.7+):
vim.api.nvim_set_hl(0, "Comment", { italic = true })

-- 2. smartindent
-- Автоматический отступ при создании новой строки.
vim.opt.smartindent = true

-- 3. autoread
-- Автоматически перезагружать файл, если он был изменён снаружи.
-- (В Neovim это работает несколько иначе, но настройка всё ещё полезна.)
vim.opt.autoread = true

-- 4. backspace
-- Чтобы backspace работал более "естественно".
vim.opt.backspace = { "indent", "eol", "start" }

-- 5. clipboard
-- "unnamedplus" позволяет использовать системный буфер обмена.
-- На некоторых системах "unnamedplus" предпочтительнее, чем "unnamed".
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

-- 12. lazyredraw
-- Иногда считалось, что позволяет ускорить макросы.
-- В Neovim часто не даёт существенной разницы. Можно оставить или закомментировать.
-- vim.opt.lazyredraw = true  -- закомментируйте, если нет разницы в производительности

-- 13. mouse-=a (отключение мыши в редакторе)
-- В Lua это проще сделать через: vim.opt.mouse = ""
-- Если хотите, чтобы мышь не работала вообще:
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
vim.opt.synmaxcol = 180

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

-- 2. undofile
-- Включаем файл для истории отмен (persistent undo).
-- Не забудьте создать папку (например ~/.local/share/nvim/undo) и указать её в undodir,
-- чтобы всё работало корректно.
vim.opt.undofile = true

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

-- ================================================
--   Пример mappings
-- ================================================

-- 1. Быстрое включение/выключение paste-режима
-- (пример из вашего конфига)
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

-- ================================================
--   Дополнительные пояснения / Устаревшие пункты
-- ================================================

-- 1. lazyredraw
--    В Neovim этот параметр почти не даёт прироста производительности.
--    Можно оставить, но зачастую не нужен.

-- 2. autoread
--    В Neovim работает, но иногда удобнее использовать плагин для авто-рефреша
--    (если вы редактируете файлы, которые часто меняются вне редактора).

-- 3. redrawtime
--    Обычно нет нужды трогать. Если у вас нет проблем с производительностью,
--    можно смело не менять.

-- 4. mouse
--    Если вы хотите отключить мышь полностью, то set mouse-=a
--    проще заменить на vim.opt.mouse = "".

-- 5. smartindent, smarttab, shiftwidth, expandtab, tabstop, softtabstop
--    В современном Neovim обычно все эти настройки выставляют в связке, если
--    вам нужны пробелы вместо табов и автоматические отступы. Так у вас и сделано.

-- 6. showmode
--    Часто отключают, чтобы не дублировать информацию, если стоит плагин типа lualine.

-- 7. viminfo
--    Не самая критичная настройка, в Neovim хранение данных идёт по-другому,
--    но обычно поддерживается и это значение.

-- 8. backspace=2
--    В .vimrc это было "set backspace=2", в Neovim принято задавать через
--    vim.opt.backspace = { "indent", "eol", "start" }.

-- 9. mapleader
--    Устанавливайте раньше загрузки плагинов. В Lua-файле обычно это делают
--    в самом начале init.lua, до того как вы вызываете `require` менеджера плагинов.

