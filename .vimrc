set nocompatible

syntax on

set ambiwidth=double
if has('mouse')
    set mouse=a
endif
set clipboard+=unnamed

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

set autoindent
set ts=4 sw=4 sts=4
set expandtab
set copyindent
set preserveindent

nnoremap o oX<C-h>
nnoremap O OX<C-h>
inoremap <CR> <CR>X<C-h>

" set title
set cmdheight=1
set laststatus=2
set showcmd
set list
set listchars=tab:^\ ,trail:\ ,eol:↲,extends:»,precedes:«,nbsp:%

" statusline
" set statusline=%t
" set statusline+=\ [%{strlen(&fenc)?&fenc:'none'}:
" set statusline+=%{&ff}]
" set statusline+=%h
" set statusline+=%m
" set statusline+=%r
" set statusline+=%y
" set statusline+=%=
" set statusline+=%c,
" set statusline+=%l/%L
" set statusline+=\ %P

augroup vimrcEx
    au BufRead * if line("'\"") > 0 && line("'\"") <= line("$") |
    \ exe "normal g`\"" | endif
augroup END
  

" NeoBundle """"""""""""""""""""""""""""""""""""""""""""""
if has('vim_starting')
    set runtimepath+=~/.vim/bundle/neobundle.vim/
endif

call neobundle#rc(expand('~/.vim/bundle/'))

NeoBundleFetch 'Shougo/neobundle.vim'
NeoBundle 'Shougo/vimproc.vim', {'build' : {'unix' : 'make -f make_unix.mak'}}
NeoBundle 'Shougo/unite.vim'
NeoBundle 'Shougo/unite-outline'
NeoBundle 'Shougo/vimshell.vim'
NeoBundle 'osyo-manga/vim-reunions'
NeoBundle 'osyo-manga/vim-marching'
NeoBundle has('lua') ? 'Shougo/neocomplete' : 'Shougo/neocomplcache'
NeoBundle 'scrooloose/nerdcommenter'
NeoBundle 'scrooloose/syntastic'
NeoBundle 'scrooloose/nerdtree'
NeoBundle 'tomasr/molokai'
NeoBundle 'mattn/emmet-vim'
NeoBundle 'tpope/vim-fugitive'
NeoBundle 'gregsexton/gitv.git'
NeoBundle 'itchyny/lightline.vim'
NeoBundle 'airblade/vim-gitgutter'

filetype plugin indent on

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

" vim-marching """"""""""""""""""""""""""""""""""""""""""
let g:marching_clang_command = '/bin/clang'
let g:marching_clang_command_option = '-std=c++1y'
let g:marching_include_paths = []
let g:marching_enable_neocomplete = 1
if !exists('g:neocomplete#force_omni_input_patterns')
    let g:neocomplete#force_omni_input_patterns = {}
endif
let g:neocomplete#force_omni_input_patterns.cpp = '[^.[:digit:] *\t]\%(\.\|->\)\w*\|\h\w*::\w*'

" NERDTree """"""""""""""""""""""""""""""""""""""""""""""
let NERDTreeShowHidden=1
if has('vim_starting') && expand("%:p") == ""
    autocmd VimEnter * execute 'NERDTree ./'
endif

" NERD Commenter """"""""""""""""""""""""""""""""""""""""
let NERDSpaceDelims=1
nmap ,, <Plug>NERDCommenterToggle
vmap ,, <Plug>NERDCommenterToggle

" syntastic """""""""""""""""""""""""""""""""""""""""""""
let g:syntastic_cpp_compiler_options = '--std=c++1y'

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

" colorscheme """""""""""""""""""""""""""""""""""""""""""
colorscheme molokai


NeoBundleCheck

