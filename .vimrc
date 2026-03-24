language C

set encoding=utf-8
set autoread
set hidden
set backspace=indent,eol,start
set fileencodings=ucs-boms,utf-8,euc-jp,cp932
set fileformats=unix,dos,mac
set autoindent
set expandtab
set cursorline
filetype plugin indent on
syntax on

augroup dotfiles_filetypes
  autocmd!
  autocmd FileType zsh,python,scala,css,scss,sass,kt setlocal sw=4 sts=4 ts=4 et
  autocmd FileType c,h,cpp,hpp,js,javascript,jsx,tsx,html,slim,ruby,typescript,yaml,yml,eruby,sql,sh,json,dart,md,er,proto setlocal sw=2 sts=2 ts=2 et
augroup END

set ignorecase
set smartcase
set incsearch
set hlsearch
