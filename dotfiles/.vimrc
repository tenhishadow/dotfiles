if !filereadable($HOME . '/.vim/autoload/plug.vim')
  silent !mkdir -p ~/.vim/{autoload,plugged} >/dev/null 2>&1
  silent !curl -fLo ~/.vim/autoload/plug.vim https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim >/dev/null 2>&1
  augroup gr_install_and_reload
    autocmd VimEnter * PlugInstall --sync | source ${MYVIMRC}
  augroup END
endif

augroup gr_install_plugins
  call plug#begin('~/.vim/plugged')
    " basic
    Plug 'itchyny/lightline.vim'            " statusline/tabline
    Plug 'scrooloose/nerdtree'
    " git
    Plug 'Xuyuanp/nerdtree-git-plugin'
    Plug 'airblade/vim-gitgutter'
    Plug 'gisphm/vim-gitignore'
    " format
    Plug 'editorconfig/editorconfig-vim'
    Plug 'junegunn/vim-easy-align'          " very easy align
    Plug 'nathanaelkane/vim-indent-guides'
    Plug 'ntpeters/vim-better-whitespace'
    Plug 'terryma/vim-multiple-cursors'
    Plug 'tomtom/tcomment_vim'              " gcc to {un}comment
    Plug 'tpope/vim-sensible'
    Plug 'dense-analysis/ale'               " https://github.com/dense-analysis/ale
    " theme
    Plug 'tomasr/molokai'
    Plug 'jacoborus/tender.vim'
    " language
    Plug 'tpope/vim-markdown'
    "" mikrotik
    Plug 'zainin/vim-mikrotik'
    "" jinja
    Plug 'glench/vim-jinja2-syntax'
    "" hashicorp
    Plug 'hashivim/vim-packer'
    Plug 'hashivim/vim-vagrant'
    Plug 'hashivim/vim-terraform'
    Plug 'juliosueiras/vim-terraform-completion'
    "" python
    Plug 'raimon49/requirements.txt.vim'
    "" ruby
    Plug 'vim-ruby/vim-ruby'
  call plug#end()
augroup END
" vint: next-line -ProhibitSetNoCompatible
set nocompatible
set shell=bash
set ttyfast
syntax on
filetype plugin indent on

" jump to the last position when reopening a file
if has('autocmd')
  augroup gr_autocmd
    au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
  augroup END
endif

" set theme
if filereadable($HOME . '/.vim/plugged/molokai/colors/molokai.vim')
  colorscheme molokai
  let g:lightline = { 'colorscheme': 'molokai' }
else
  augroup gr_source
    autocmd VimEnter * PlugInstall --sync | source ${MYVIMRC}
  augroup END
  colorscheme koehler
  let g:lightline = { 'colorscheme': 'koehler' }
endif

" Ignore whitespace in vimdiff.
if &diff
  set diffopt+=iwhite
endif

set autoread                      " re-read changed file
set autoindent
set smartindent
set termguicolors                 " show me all the colors please
set smartindent
set tabstop=2                     " set indent to 2 spaces
set shiftwidth=2
set smarttab
set expandtab                     " use spaces, not tab characters
set ignorecase                    " ignore case in search
set showmatch                     " show bracket matches
set hlsearch                      " highlight all search matches
set number                        " show line numbers
set smartcase                     " pay attention to case when caps are used
set incsearch                     " show search results as I type
set ruler                         " show row and column in footer
set clipboard=unnamed             " use the system clipboard
set wildmenu                      " enable bash style tab completion
set wildmode=list:longest,full
set backspace=2                   " make backspace work like most other programs
set mouse-=a                      " do not use visual mode for mouse select

nnoremap <F2> :set invpaste paste?<CR>
set pastetoggle=<F2>
set showmode

augroup gr_filetype " filetypes
" Fastlane
au BufNewFile,BufRead Appfile       set ft=ruby
au BufNewFile,BufRead Fastfile      set ft=ruby
au BufNewFile,BufRead Matchfile     set ft=ruby
" ansible
au BufNewFile,BufRead .ansible-lint set ft=yaml
au BufNewFile,BufRead .yamllint     set ft=yaml
augroup END
" per plugin
" NERDTree
let NERDTreeAutoDeleteBuffer = 1 " Automatically delete the buffer of the file you just deleted with NerdTree
let NERDTreeShowHidden       = 1 " show hidden files
let NERDTreeQuitOnOpen       = 1 " Closing automatically
let NERDTreeMinimalUI        = 1
let NERDTreeDirArrows        = 1

" EasyAlign maps
" Start interactive EasyAlign in visual mode (e.g. vipga)
xmap ga <Plug>(EasyAlign)
" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)
