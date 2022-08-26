if !filereadable($HOME . '/.vim/autoload/plug.vim')
  if !executable('curl')
    echoerr 'ERR: you have to install curl or first install vim-plug yourself!'
    execute 'q!'
  endif
  " echo 'DBG: installing Vim-Plug...'
  silent !mkdir -p ~/.vim/{autoload,plugged} >/dev/null 2>&1
  silent !curl -fLo ~/.vim/autoload/plug.vim https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim >/dev/null 2>&1
  augroup gr_install_and_reload
    autocmd VimEnter * PlugInstall --sync | source ${MYVIMRC}
  augroup END
endif

if !filereadable($HOME . '/.vim/undodir')
  silent !mkdir -p ~/.vim/undodir >/dev/null 2>&1
endif

augroup gr_install_plugins
  call plug#begin('~/.vim/plugged')
    " basic
    Plug 'itchyny/lightline.vim'            " statusline/tabline
    Plug 'scrooloose/nerdtree'
    Plug 'mbbill/undotree'
    " git
    Plug 'Xuyuanp/nerdtree-git-plugin'
    Plug 'airblade/vim-gitgutter'
    Plug 'gisphm/vim-gitignore'
    Plug 'tpope/vim-fugitive'
    " format
    Plug 'editorconfig/editorconfig-vim'    " support .editorconfig in vim
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
    Plug 'Valloric/YouCompleteMe', { 'do': './install.py' }
    "" markdown
    Plug 'tpope/vim-markdown'
    Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }, 'for': ['markdown', 'vim-plug']}  " :MarkdownPreview
    "" mikrotik
    Plug 'zainin/vim-mikrotik'
    "" jinja
    Plug 'glench/vim-jinja2-syntax'
    "" hashicorp
    Plug 'hashivim/vim-consul'
    Plug 'hashivim/vim-nomadproject'
    Plug 'hashivim/vim-packer'
    Plug 'hashivim/vim-terraform'
    Plug 'hashivim/vim-vagrant'
    Plug 'hashivim/vim-vaultproject'
    "" python
    Plug 'raimon49/requirements.txt.vim'
    Plug 'pearofducks/ansible-vim', { 'do': './UltiSnips/generate.sh' }
    "" ruby
    Plug 'vim-ruby/vim-ruby'
    "" nginx
    Plug 'chr4/nginx.vim'
  call plug#end()
augroup END

" vint: next-line -ProhibitSetNoCompatible
set nocompatible
set shell=bash
set ttyfast
syntax on

" folding
set foldmethod=syntax
set foldlevelstart=1

let javaScript_fold=1         " JavaScript
let perl_fold=1               " Perl
let ruby_fold=1               " Ruby
let sh_fold_enabled=1         " sh
let vimsyn_folding='af'       " Vim script
let xml_syntax_folding=1      " XML
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

augroup gr_hacks
  au BufEnter * set fo-=c fo-=r fo-=o                    " stop annoying auto commenting on new lines
augroup END

highlight Comment gui=italic cterm=italic              " italic comments

set smartindent
set autoread          " re-read changed file
set backspace=2       " make backspace work like most other programs
set clipboard=unnamed " use the system clipboard
set expandtab         " use spaces, not tab characters
set history=1000      " history limit
set viminfo='100,<500,s10,h
set hlsearch          " highlight all search matches
set ignorecase        " ignore case in search
set incsearch         " show search results as I type
set lazyredraw        " no redraw wihle executing macros,...
set mouse-=a          " do not use visual mode for mouse select
set number            " show line numbers
set redrawtime=10000  " redraw time
set ruler             " show row and column in footer
set shiftwidth=2
set showmatch         " show bracket matches
set smartcase         " pay attention to case when caps are used
set smartindent
set smartindent
set smarttab
set synmaxcol=180     " avoid very slow redrawing
set tabstop=2 softtabstop=2         " set indent to 2 spaces
set termguicolors     " show me all the colors please
set wildmenu          " enable bash style tab completion
set wildmode=list:longest,full
" for undo
set noswapfile
set nobackup
set undodir=~/.vim/undodir
set undofile
nnoremap <leader>u ::UndotreeShow<CR>

nnoremap <F2> :set invpaste paste?<CR>
set pastetoggle=<F2>
set showmode

" other remaps
let mapleader = ''
" nnoremap <leader>h :wincmd h<CR>
" nnoremap <leader>j :wincmd j<CR>
" nnoremap <leader>k :wincmd k<CR>
" nnoremap <leader>l :wincmd l<CR>
" panel resize
nnoremap <silent><leader>= :vertical resize +5<CR>
nnoremap <silent><leader>- :vertical resize -5<CR>


" redefine filetypes
augroup gr_filetype " filetypes
  " Fastlane
  au BufNewFile,BufRead Appfile       set ft=ruby
  au BufNewFile,BufRead Fastfile*     set ft=ruby
  au BufNewFile,BufRead Matchfile     set ft=ruby
  " ansible
  au BufNewFile,BufRead .ansible-lint set ft=yaml
  au BufNewFile,BufRead .yamllint     set ft=yaml
  " terragrunt
  au BufNewFile,BufRead terragrunt.hcl set ft=terraform
  " custom ssh configs
  au BufNewFile,BufRead ~/.ssh/config.d/* set ft=sshconfig
  " docker
  au BufNewFile,BufRead Dockerfile*     set ft=dockerfile
augroup END

" per plugin configuration

"" NERDTree
let NERDTreeAutoDeleteBuffer = 1 " Automatically delete the buffer of the file you just deleted with NerdTree
let NERDTreeDirArrows        = 1
let NERDTreeMinimalUI        = 1
let NERDTreeQuitOnOpen       = 1 " Closing automatically
let NERDTreeShowHidden       = 1 " show hidden files

"" EasyAlign maps
" Start interactive EasyAlign in visual mode (e.g. vipga)
xmap ga <Plug>(EasyAlign)
" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)
