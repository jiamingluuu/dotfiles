set number
set expandtab
set tabstop=2
set cursorline
set shiftwidth=2
set softtabstop=2
set autoindent
set scrolloff=4
set ttimeoutlen=0
set notimeout
set viewoptions=cursor,folds,slash,unix
set nowrap
set tw=0
set indentexpr=
set foldmethod=indent
set foldlevel=99
set foldenable
set formatoptions-=tc
set splitright
set splitbelow
set noshowmode
set showcmd
set wildmenu
set ignorecase
set smartcase
set cc=80
set guifont=Menlo:h14
colorscheme zellner

let g:neoterm_autoscroll = 1
let g:terminal_color_0   = '#000000'
let g:terminal_color_1   = '#FF5555'
let g:terminal_color_2   = '#50FA7B'
let g:terminal_color_3   = '#F1FA8C'
let g:terminal_color_4   = '#BD93F9'
let g:terminal_color_5   = '#FF79C6'
let g:terminal_color_6   = '#8BE9FD'
let g:terminal_color_7   = '#BFBFBF'
let g:terminal_color_8   = '#4D4D4D'
let g:terminal_color_9   = '#FF6E67'
let g:terminal_color_10  = '#5AF78E'
let g:terminal_color_11  = '#F4F99D'
let g:terminal_color_12  = '#CAA9FA'
let g:terminal_color_13  = '#FF92D0'
let g:terminal_color_14  = '#9AEDFE'

let mapleader=" "
noremap Q :q<CR>
noremap S :w<CR>
noremap <LEADER><CR> :nohlsearch<CR>
noremap <silent> H 0
noremap <silent> K 5k
noremap <silent> J 5j
noremap <silent> L $
noremap <silent> C J

noremap <up> :res +5<CR>
noremap <down> :res -5<CR>
noremap <left> :vertical resize-5<CR>
noremap <right> :vertical resize+5<CR>

noremap <LEADER>w <C-w>w
noremap <LEADER>h <C-w>h
noremap <LEADER>j <C-w>j
noremap <LEADER>k <C-w>k
noremap <LEADER>l <C-w>l

noremap tn :tabe<CR>
noremap th :-tabnext<CR>
noremap tl :+tabnext<CR>
noremap <LEADER>sc :set spell!<CR>
