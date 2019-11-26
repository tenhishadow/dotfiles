call plug#begin('~/.vim/plugged')
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

" per plugin
" NERDTree
let NERDTreeAutoDeleteBuffer = 1
let NERDTreeShowHidden=1