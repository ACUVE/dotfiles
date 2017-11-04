set ambiwidth=double

if has('mouse')
  set mouse=a
endif

set wildmode=longest,full
if has('nvim')
  set clipboard+=unnamedplus
else
  set clipboard=unnamed,autoselect
endif

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

" maybe don't autofold anything
set foldlevel=100

set cmdheight=1
set laststatus=2
set showcmd
set list
set listchars=tab:^-,trail:\ ,eol:↲,extends:»,precedes:«,nbsp:%

augroup vimrcEx
    au BufRead * if line("'\"") > 0 && line("'\"") <= line("$") |
    \ exe "normal g`\"" | endif
augroup END
