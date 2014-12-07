set nocompatible

syntax on

set ambiwidth=double
if has('mouse')
    set mouse=a
endif
" set clipboard+=unnamed

set backspace=indent,eol,start

set ignorecase
set smartcase
set wrapscan
set incsearch
set hlsearch

set number
set ruler
set showmatch
set cursorline
set scrolloff=2
set hidden
set wrap

set autoindent
set ts=4 sw=4 sts=4
set expandtab
set copyindent
set preserveindent

set splitbelow
set splitright

set fileencodings=utf-8,sjis,euc-jp,iso-2022-jp
set fileformats=unix,dos,mac

nnoremap <silent> <Esc><Esc> :nohlsearch<CR>

nnoremap o oX<C-h>
nnoremap O OX<C-h>
inoremap <CR> <CR>X<C-h>

nnoremap s <Nop>

nnoremap <silent> j gj
nnoremap <silent> k gk
nnoremap <silent> <Down> gj
nnoremap <silent> <Up> gk
nnoremap <silent> gj j
nnoremap <silent> gk k

nnoremap <silent> n nzz
nnoremap <silent> N Nzz

" ウィンドウ分割関連
nnoremap <silent> s <Nop>

nnoremap <silent> ss :split<CR>
nnoremap <silent> sv :vsplit<CR>
nnoremap <silent> sh <C-w>h
nnoremap <silent> sj <C-w>j
nnoremap <silent> sk <C-w>k
nnoremap <silent> sl <C-w>l

nnoremap <silent> sH <C-w>H
nnoremap <silent> sJ <C-w>J
nnoremap <silent> sK <C-w>K
nnoremap <silent> sL <C-w>L
nnoremap <silent> sr <C-w>r

nnoremap <silent> st :tabnew<CR>
nnoremap <silent> sn gt
nnoremap <silent> sp gT

nnoremap <silent> sq :q<CR>
nnoremap <silent> sQ :bd<CR>

nnoremap <silent> so <C-w>o

nnoremap <silent> sT :Unite tab<CR>
nnoremap <silent> sb :Unite buffer_tab -buffer-name=file<CR>
nnoremap <silent> sB :Unite buffer -buffer-name=file<CR>


" set title
set cmdheight=1
set laststatus=2
set showcmd
set list
set listchars=tab:^-,trail:\ ,eol:↲,extends:»,precedes:«,nbsp:%

augroup vimrcEx
    au BufRead * if line("'\"") > 0 && line("'\"") <= line("$") |
    \ exe "normal g`\"" | endif
augroup END
  

" NeoBundle """"""""""""""""""""""""""""""""""""""""""""""
if has('vim_starting')
    set runtimepath+=~/.vim/bundle/neobundle.vim/
endif

call neobundle#begin(expand('~/.vim/bundle/'))

NeoBundleFetch 'Shougo/neobundle.vim'
NeoBundle 'Shougo/vimproc.vim', {'build' : {'unix' : 'make -f make_unix.mak'}}
NeoBundle 'Shougo/unite.vim'
NeoBundle 'Shougo/unite-outline'
NeoBundle 'Shougo/tabpagebuffer.vim'
NeoBundle 'Shougo/vimshell.vim'
NeoBundle 'Shougo/vimfiler.vim'
NeoBundle 'Shougo/neosnippet'
NeoBundle 'Shougo/neosnippet-snippets'
NeoBundle 'osyo-manga/vim-reunions'
NeoBundle 'osyo-manga/vim-marching'
NeoBundle has('lua') ? 'Shougo/neocomplete' : 'Shougo/neocomplcache'
NeoBundle 'scrooloose/nerdcommenter'
NeoBundle 'scrooloose/syntastic'
NeoBundle 'tomasr/molokai'
NeoBundle 'mattn/emmet-vim'
NeoBundle 'tpope/vim-fugitive'
NeoBundle 'gregsexton/gitv.git'
NeoBundle 'itchyny/lightline.vim'
NeoBundle 'airblade/vim-gitgutter'
NeoBundle 'Lokaltog/vim-easymotion'
NeoBundle 'kana/vim-submode'
" NeoBundle 'MetalPhaeton/easybracket-vim'

call neobundle#end()


" filetype plugin indent on
filetype plugin on

" vim-submode """""""""""""""""""""""""""""""""""""""""""
call submode#enter_with('bufmove', 'n', '', 's>', '<C-w>>')
call submode#enter_with('bufmove', 'n', '', 's<', '<C-w><')
call submode#enter_with('bufmove', 'n', '', 's+', '<C-w>+')
call submode#enter_with('bufmove', 'n', '', 's-', '<C-w>-')
call submode#map('bufmove', 'n', '', '>', '<C-w>>')
call submode#map('bufmove', 'n', '', '<', '<C-w><')
call submode#map('bufmove', 'n', '', '+', '<C-w>+')
call submode#map('bufmove', 'n', '', '-', '<C-w>-')

" neocomplete / neocomplcache """"""""""""""""""""""""""""
if neobundle#is_installed('neocomplete')
    " neocmplete用設定
    let g:neocomplete#enable_at_startup = 1
    let g:neocomplete#enable_ignore_case = 1
    let g:neocomplete#enable_smart_case = 1
    if !exists('g:neocomplete#keyword_patterns')
        let g:neocomplete#keyword_patterns = {}
    endif
    let g:neocomplete#keyword_patterns._ = '\h\w*'
elseif neobundle#is_installed('neocomplcache')
    " neocomplcache用設定
    let g:neocomplcache_enable_at_startup = 1
    let g:neocomplcache_enable_ignore_case = 1
    let g:neocomplcache_enable_smart_case = 1
    if !exists('g:neocomplcache_keyword_patterns')
        let g:neocomplcache_keyword_patterns = {}
    endif
    let g:neocomplcache_keyword_patterns._ = '\h\w*'
    let g:neocomplcache_enable_camel_case_completion = 1
    let g:neocomplcache_enable_underbar_completion = 1
endif

" VimFiler """"""""""""""""""""""""""""""""""""""""""""""
let g:vimfiler_as_default_explorer = 1
nnoremap <silent> <Space>f :VimFiler -split -simple -winwidth=30 -no-quit<CR>

if has('vim_starting') && expand("%:p") == ""
    autocmd VimEnter * VimFiler -split -simple -winwidth=30 -no-quit
endif


" vim-marching """"""""""""""""""""""""""""""""""""""""""
let g:marching_clang_command = '/bin/clang'
let g:marching_clang_command_option = '-std=c++1y -I/usr/lib64/qt5/mkspecs/linux-g++-64 -I/usr/include/qt5 -I/usr/include/qt5/QtWebKitWidgets -I/usr/include/qt5/QtQuick -I/usr/include/qt5/QtOpenGL -I/usr/include/qt5/QtPrintSupport -I/usr/include/qt5/QtQml -I/usr/include/qt5/QtWebKit -I/usr/include/qt5/QtWidgets -I/usr/include/qt5/QtNetwork -I/usr/include/qt5/QtGui -I/usr/include/qt5/QtCore'
let g:marching_include_paths = []
let g:marching_enable_neocomplete = 1
if !exists('g:neocomplete#force_omni_input_patterns')
    let g:neocomplete#force_omni_input_patterns = {}
endif
" let g:neocomplete#force_omni_input_patterns.cpp = '[^.[:digit:] *\t]\%(\.\|->\)\w*\|\h\w*::\w*'

" http://d.hatena.ne.jp/osyo-manga/20131029/1383050380 を参照のこと
" filetype=cpp で insert mode から抜けるたびにキャッシュを削除する
augroup cpp
    autocmd!
    autocmd FileType cpp call s:cpp()
augroup END

imap <C-o><C-n> <Plug>(marching_start_omni_complete)

function! s:cpp()
    augroup filetype-cpp
        autocmd! * <buffer>
        autocmd InsertLeave <buffer> MarchingBufferClearCache
    augroup END
endfunction

" NERD Commenter """"""""""""""""""""""""""""""""""""""""
let NERDSpaceDelims=1
nmap ,, <Plug>NERDCommenterToggle
vmap ,, <Plug>NERDCommenterToggle

" syntastic """""""""""""""""""""""""""""""""""""""""""""
let g:syntastic_cpp_compiler_options = g:marching_clang_command_option

" lightline """""""""""""""""""""""""""""""""""""""""""""
let g:lightline = {
      \ 'active': {
      \   'left': [ ['mode', 'paste'], ['readonly', 'filename', 'modified'] ]
      \ },
      \ 'component_function': {
      \   'mode': 'MyMode'
      \ }
      \ }
function! MyMode()
      return  &ft == 'unite' ? 'Unite' :
            \ &ft == 'vimfiler' ? 'VimFiler' :
            \ &ft == 'vimshell' ? 'VimShell' :
            \ winwidth(0) > 60 ? lightline#mode() : ''
endfunction

" easymotion """"""""""""""""""""""""""""""""""""""""""""
map f <Plug>(easymotion-fl)
map t <Plug>(easymotion-tl)
map F <Plug>(easymotion-Fl)
map T <Plug>(easymotion-Tl)
nmap <Space>s <Plug>(easymotion-s2)
xmap <Space>s <Plug>(easymotion-s2)
omap <Space>s <Plug>(easymotion-s2)

nmap g/ <Plug>(easymotion-sn)
xmap g/ <Plug>(easymotion-sn)
omap g/ <Plug>(easymotion-tn)

map ,j <Plug>(easymotion-j)
map ,k <Plug>(easymotion-k)

let g:EasyMotion_smartcase = 1
let g:EasyMotion_startofline = 0

" neosnippet """"""""""""""""""""""""""""""""""""""""""""
imap <C-k> <Plug>(neosnippet_expand_or_jump)
smap <C-k> <Plug>(neosnippet_expand_or_jump)
xmap <C-k> <Plug>(neosnippet_expand_target)

imap <expr><Tab> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: pumvisible() ? "\<C-n>" : "\<Tab>"
smap <expr><Tab> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: "\<Tab>"

if has('conceal')
    set conceallevel=2 concealcursor=i
endif

" colorscheme """""""""""""""""""""""""""""""""""""""""""
colorscheme molokai

NeoBundleCheck
