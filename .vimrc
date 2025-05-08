" General
language C

set fenc=utf-8
set nobackup
set noswapfile
set autoread
set hidden
set showcmd
set clipboard=unnamed
set wildignore+=log/**,tmp/**,vendor/**,.bundle/**,bundle/**,.git/**,node_modules/**,flow-typed/**,public/**,database_storage/**,mysql/data/**,internal/app/mysql/data/**,pb/**
set backspace=indent,eol,start
set fileencoding=utf-8
set fileencodings=ucs-boms,utf-8,euc-jp,cp932
set fileformats=unix,dos,mac
set ambiwidth=double
set nocompatible
set wildmenu

set showmatch
set cursorline
set wildmode=list:longest
nnoremap j gj
nnoremap k gk
set wrap
set autoindent
set smartindent
set smarttab
set expandtab
filetype plugin on
filetype indent on
autocmd FileType c           setlocal sw=4 sts=4 ts=4 et
autocmd FileType js          setlocal sw=2 sts=2 ts=2 et
autocmd FileType jsx         setlocal sw=2 sts=2 ts=2 et
autocmd FileType tsx         setlocal sw=2 sts=2 ts=2 et
autocmd FileType zsh         setlocal sw=4 sts=4 ts=4 et
autocmd FileType python      setlocal sw=4 sts=4 ts=4 et
autocmd FileType scala       setlocal sw=4 sts=4 ts=4 et
autocmd FileType json        setlocal sw=4 sts=4 ts=4 et
autocmd FileType css         setlocal sw=4 sts=4 ts=4 et
autocmd FileType scss        setlocal sw=4 sts=4 ts=4 et
autocmd FileType sass        setlocal sw=4 sts=4 ts=4 et
autocmd FileType kt          setlocal sw=4 sts=4 ts=4 et
autocmd FileType html        setlocal sw=2 sts=2 ts=2 et
autocmd FileType slim        setlocal sw=2 sts=2 ts=2 et
autocmd FileType ruby        setlocal sw=2 sts=2 ts=2 et
autocmd FileType javascript  setlocal sw=2 sts=2 ts=2 et
autocmd FileType typescript  setlocal sw=2 sts=2 ts=2 et
autocmd FileType yaml        setlocal sw=2 sts=2 ts=2 et
autocmd FileType yml         setlocal sw=2 sts=2 ts=2 et
autocmd FileType eruby       setlocal sw=2 sts=2 ts=2 et
autocmd FileType sql         setlocal sw=2 sts=2 ts=2 et
autocmd FileType sh          setlocal sw=2 sts=2 ts=2 et
autocmd FileType c           setlocal sw=2 sts=2 ts=2 et
autocmd FileType h           setlocal sw=2 sts=2 ts=2 et
autocmd FileType cpp         setlocal sw=2 sts=2 ts=2 et
autocmd FileType hpp         setlocal sw=2 sts=2 ts=2 et
autocmd FileType json        setlocal sw=2 sts=2 ts=2 et
autocmd FileType dart        setlocal sw=2 sts=2 ts=2 et
autocmd FileType md          setlocal sw=2 sts=2 ts=2 et
autocmd FileType er          setlocal sw=2 sts=2 ts=2 et
autocmd FileType proto       setlocal sw=2 sts=2 ts=2 et

set ignorecase
set smartcase
set incsearch
set wrapscan
set hlsearch
nmap <Esc><Esc> :nohlsearch<CR><Esc>

" Plugins
" :PlugInstall
call plug#begin('~/.vim/plugged')
" Go
Plug 'prabirshrestha/async.vim'
Plug 'prabirshrestha/asyncomplete.vim'
Plug 'prabirshrestha/asyncomplete-lsp.vim'
Plug 'prabirshrestha/vim-lsp'
Plug 'mattn/vim-lsp-settings'
Plug 'mattn/vim-goimports'
" StatsuLine
Plug 'itchyny/lightline.vim'
Plug 'hashivim/vim-terraform'
call plug#end()

autocmd BufWritePre *.{yml,yaml,py,rb,go,js,ts} :%s/\s\+$//e
autocmd BufWritePre <buffer> LspDocumentFormatSync
autocmd BufNewFile,BufRead *.{html,htm,erb,slim,jsx,tsx,vue*} set filetype=html

set statusline=%F
set statusline+=%m
set statusline+=%r
set statusline+=%h
set statusline+=%w
set statusline+=%=
set statusline+=[ENC=%{&fileencoding}]
set statusline+=[LOW=%l/%L]
set laststatus=2

" Use all the defaults (recommended):
let g:lsc_auto_map = v:true

" Apply the defaults with a few overrides:
let g:lsc_auto_map = {'defaults': v:true, 'FindReferences': '<leader>r'}

" Setting a value to a blank string leaves that command unmapped:
let g:lsc_auto_map = {'defaults': v:true, 'FindImplementations': ''}

" ... or set only the commands you want mapped without defaults.
" Complete default mappings are:
let g:lsc_auto_map = {
    \ 'GoToDefinition': '<C-]>',
    \ 'GoToDefinitionSplit': ['<C-W>]', '<C-W><C-]>'],
    \ 'FindReferences': 'gr',
    \ 'NextReference': '<C-n>',
    \ 'PreviousReference': '<C-p>',
    \ 'FindImplementations': 'gI',
    \ 'FindCodeActions': 'ga',
    \ 'Rename': 'gR',
    \ 'ShowHover': v:true,
    \ 'DocumentSymbol': 'go',
    \ 'WorkspaceSymbol': 'gS',
    \ 'SignatureHelp': 'gm',
    \ 'Completion': 'completefunc',
    \}

" Terraform
let g:terraform_align=1
let g:terraform_fold_sections=1
let g:terraform_remap_spacebar=1
let g:terraform_commentstring='//%s'
let g:terraform_fmt_on_save=1

" Markdown
let g:mkdp_auto_start = 1
let g:mkdp_auto_close = 1
let g:mkdp_theme = 'light'

syntax off
