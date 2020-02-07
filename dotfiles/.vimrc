if empty(glob('~/.vim/plugged'))
  autocmd VimEnter * PlugInstall --sync | source ${MYVIMRC}
endif

call plug#begin('~/.vim/plugged')
  Plug 'junegunn/vim-easy-align' " very easy align
  Plug 'scrooloose/nerdtree'
  Plug 'Xuyuanp/nerdtree-git-plugin'
  Plug 'tpope/vim-sensible'
  Plug 'itchyny/lightline.vim'
  Plug 'ntpeters/vim-better-whitespace'
  Plug 'editorconfig/editorconfig-vim'
  Plug 'airblade/vim-gitgutter'
  Plug 'junegunn/vim-easy-align'
  Plug 'nathanaelkane/vim-indent-guides'
  Plug 'tomtom/tcomment_vim'
  Plug 'terryma/vim-multiple-cursors'
  Plug 'dense-analysis/ale'      " https://github.com/dense-analysis/ale
  Plug 'hashivim/vim-terraform'
  Plug 'hashivim/vim-packer'
  Plug 'hashivim/vim-vagrant'
  Plug 'glench/vim-jinja2-syntax'
call plug#end()

set nocompatible
syntax on                         " show syntax highlighting
filetype plugin indent on
colorscheme koehler

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

" filetypes
" Fastlane
au BufNewFile,BufRead Appfile       set ft=ruby
au BufNewFile,BufRead Fastfile      set ft=ruby
au BufNewFile,BufRead Matchfile     set ft=ruby

" per plugin
" NERDTree
let NERDTreeAutoDeleteBuffer = 1 " Automatically delete the buffer of the file you just deleted with NerdTree
let NERDTreeShowHidden       = 1 " show hidden files
let NERDTreeQuitOnOpen       = 1 " Closing automatically
let NERDTreeMinimalUI        = 1
let NERDTreeDirArrows        = 1

" EasyAlign
" Start interactive EasyAlign in visual mode (e.g. vipga)
xmap ga <Plug>(EasyAlign)
" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)
