" General
" 言語設定
language C
" 文字コードをUFT-8に設定
set fenc=utf-8
" バックアップファイルを作らない
set nobackup
" スワップファイルを作らない
set noswapfile
" 編集中のファイルが変更されたら自動で読み直す
set autoread
" バッファが編集中でもその他のファイルを開けるように
set hidden
" 入力中のコマンドをステータスに表示する
set showcmd
" OSのクリップボードを使う
set clipboard=unnamed
" vimgrepから除外
set wildignore+=log/**,tmp/**,vendor/**,.bundle/**,bundle/**,.git/**,node_modules/**,flow-typed/**,public/**,database_storage/**,mysql/data/**
" バックスペースキーの有効化
set backspace=indent,eol,start
" 保存時の文字コード
set fileencoding=utf-8
" 読み込み時の文字コードの自動判別. 左側が優先される
set fileencodings=ucs-boms,utf-8,euc-jp,cp932
" 改行コードの自動判別. 左側が優先される
set fileformats=unix,dos,mac
" □や○文字が崩れる問題を解決
set ambiwidth=double
" NERDTreeでdotfilesを表示する
let NERDTreeShowHidden=1

set nocompatible
set wildmenu

" Interface
" 括弧入力時の対応する括弧を表示
set showmatch
" 現在の行を強調表示
set cursorline
" コマンドラインの補完
set wildmode=list:longest
" 折り返し時に表示行単位での移動できるようにする
nnoremap j gj
nnoremap k gk
" カラースキーム
autocmd ColorScheme * highlight Comment ctermfg=15
autocmd ColorScheme * highlight Todo term=standout ctermfg=17 ctermbg=7 guifg=Blue guibg=Yellow
colorscheme delek
syntax enable
" ウィンドウの幅より長い行は折り返され、次の行に続けて表示される
set wrap
" 補完の色設定
hi Pmenu ctermbg=4
hi PmenuSel ctermbg=2
hi PmenuSbar ctermbg=2
hi PmenuThumb ctermfg=3


" Indent
" 改行時に前の行のインデントを継続する
set autoindent
" 改行時に前の行の構文をチェックし次の行のインデントを増減する
set smartindent
" 新しい行を作ったときに高度な自動インデントを行う
set smarttab
" タブ入力を複数の空白入力に置き換える
set expandtab
"ファイルタイプの検索を有効にする
filetype plugin on
"ファイルタイプに合わせたインデントを利用
filetype indent on
"sw=softtabstop, sts=shiftwidth, ts=tabstop, et=expandtabの略
autocmd FileType c           setlocal sw=4 sts=4 ts=4 et
autocmd FileType js          setlocal sw=4 sts=4 ts=4 et
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


" Search
" 検索文字列が小文字の場合は大文字小文字を区別なく検索する
set ignorecase
" 検索文字列に大文字が含まれている場合は区別して検索する
set smartcase
" 検索文字列入力時に順次対象文字列にヒットさせる
set incsearch
" 検索時に最後まで行ったら最初に戻る
set wrapscan
" 検索語をハイライト表示
set hlsearch
" ESC連打でハイライト解除
nmap <Esc><Esc> :nohlsearch<CR><Esc>


" Language
" Goで保存時にいろいろ実行する
let g:go_fmt_command = "goimports"
let g:go_metalinter_autosave = 1
" let g:go_metalinter_autosave_enabled = ['vet']

" Dartで保存時にformatする
function! _DartFmt()
  exe ":DartFmt"
endfunction
command! CheckCode call _DartFmt()
autocmd BufWrite *.{dart} :CheckCode
nnoremap <leader>da :DartAnalyzer<cr>


" Plugins
" :PlugInstall
call plug#begin('~/.vim/plugged')
" Go
Plug 'fatih/vim-go', { 'do': ':GoInstallBinaries' }
" TypeScript
Plug 'leafgarland/typescript-vim'
" StatsuLine
Plug 'itchyny/lightline.vim'
" GoSnipet
Plug 'SirVer/ultisnips'
" Rails
Plug 'tpope/vim-rails'
" NERDTree
Plug 'scrooloose/nerdtree'
" Terraform
Plug 'hashivim/vim-terraform'
" C++
Plug 'vim-jp/cpp-vim'
Plug 'justmao945/vim-clang'
" Kotlin
Plug 'udalov/kotlin-vim'
" golsp
Plug 'prabirshrestha/async.vim'
Plug 'prabirshrestha/vim-lsp'
Plug 'prabirshrestha/asyncomplete.vim'
Plug 'prabirshrestha/asyncomplete-lsp.vim'
Plug 'natebosch/vim-lsc'
" Dart
Plug 'dart-lang/dart-vim-plugin'
" Flutter
Plug 'thosakwe/vim-flutter'
call plug#end()

" Autocmd
" 無駄な空白を削除
autocmd BufWritePre *.{yml,yaml,py,rb,go,js,ts} :%s/\s\+$//e
" HTML
autocmd BufNewFile,BufRead *.{html,htm,erb,slim,vue*} set filetype=html

" StatusLine
" ファイル名表示
set statusline=%F
" 変更チェック表示
set statusline+=%m
" 読み込み専用かどうか表示
set statusline+=%r
" ヘルプページなら[HELP]と表示
set statusline+=%h
" プレビューウインドウなら[Prevew]と表示
set statusline+=%w
" これ以降は右寄せ表示
set statusline+=%=
" file encoding
set statusline+=[ENC=%{&fileencoding}]
" 現在行数/全行数
set statusline+=[LOW=%l/%L]
" ステータスラインを常に表示(0:表示しない、1:2つ以上ウィンドウがある時だけ表示)
set laststatus=2


" Aliases
:command Ge GoErrCheck
:command NT NERDTree

" Terraform
let g:terraform_align=1
let g:terraform_fold_sections=1
let g:terraform_remap_spacebar=1
let g:terraform_commentstring='//%s'
let g:terraform_fmt_on_save=1

" Clang
function! s:clang_format()
  let now_line = line(".")
  exec ":%! clang-format -style=Google"
  exec ":" . now_line
endfunction

if executable('clang-format')
  augroup cpp_clang_format
    autocmd!
    autocmd BufWrite,FileWritePre,FileAppendPre *.[ch]pp call s:clang_format()
  augroup END
endif

" golsp
" if executable('golsp')
"   augroup LspGo
"     au!
"     autocmd User lsp_setup call lsp#register_server({
"         \ 'name': 'go-lang',
"         \ 'cmd': {server_info->['golsp', '-mode', 'stdio']},
"         \ 'whitelist': ['go'],
"         \ })
"     autocmd FileType go setlocal omnifunc=lsp#complete
"   augroup END
" endif

let g:lsp_async_completion = 1
if executable('gopls')
  augroup LspGo
    au!
    autocmd User lsp_setup call lsp#register_server({
        \ 'name': 'go-lang',
        \ 'cmd': {server_info->['gopls']},
        \ 'whitelist': ['go'],
        \ 'workspace_config': {'gopls': {
        \     'staticcheck': v:true,
        \     'completeUnimported': v:true,
        \     'caseSensitiveCompletion': v:true,
        \     'usePlaceholders': v:true,
        \     'completionDocumentation': v:true,
        \     'watchFileChanges': v:true,
        \     'hoverKind': 'SingleLine',
        \   }},
        \ })
    autocmd FileType go setlocal omnifunc=lsp#complete
    autocmd FileType go nmap <buffer> gd <plug>(lsp-definition)
    autocmd FileType go nmap <buffer> ,n <plug>(lsp-next-error)
    autocmd FileType go nmap <buffer> ,p <plug>(lsp-previous-error)
  augroup END
endif
