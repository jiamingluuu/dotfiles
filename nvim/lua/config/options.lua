-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
local opt = vim.opt -- for conciseness
opt.guifont = { "MesloLGLDZ NFM", "h12" }
-- line numbers
opt.number = true
opt.relativenumber = false

opt.so = 8
-- opt.tabstop = 4 -- A TAB character looks like 4 spaces
-- opt.expandtab = true -- Pressing the TAB key will insert spaces instead of a TAB character
-- opt.softtabstop = 4 -- Number of spaces inserted instead of a TAB character
-- opt.shiftwidth = 4 -- Number of spaces inserted when indenting
opt.expandtab = true

-- line wrapping
opt.wrap = false

-- search setting
opt.ignorecase = true
opt.smartcase = true

-- cursor line
opt.cursorline = true

-- appearance
opt.termguicolors = true
opt.background = "dark"
opt.signcolumn = "yes"
opt.colorcolumn = "80,120"

-- clipboard
opt.clipboard = "unnamedplus"

-- split windos
opt.splitright = true
opt.splitbelow = true

opt.conceallevel = 0

opt.iskeyword:append("-")

-- codes auto-folded after downloading nvim-treesitter, so the following is added
opt.foldlevel = 999
opt.laststatus = 0

