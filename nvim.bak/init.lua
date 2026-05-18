-- bootstrap lazy.nvim, LazyVim and your plugins
if not vim.g.vscode then
  require("config.lazy")
else
  local map = vim.keymap.set

  map("n", "H", "0")
  map("n", "J", "5j")
  map("n", "K", "5k")
  map("n", "L", "$")
  map("n", "C", "J")

  map("v", "H", "0")
  map("v", "J", "5j")
  map("v", "K", "5k")
  map("v", "L", "$")

  map("n", "Q", "<cmd>q<CR>")
  map("n", "S", "<cmd>w<CR>")

  map("n", "<leader><CR>", "<cmd>nohl<CR>")
  map("n", "<leader>sc", "<cmd>set spell!<CR>")

  map("n", "tn", "<cmd>tabe<CR>")
  map("n", "th", "<cmd>-tabnext<CR>")
  map("n", "tl", "<cmd>+tabnext<CR>")

  map("n", "sh", "<cmd>set nosplitright<CR><cmd>vsplit<CR>")
  map("n", "sl", "<cmd>set splitright<CR><cmd>vsplit<CR>")
  map("n", "sj", "<cmd>set splitbelow<CR><cmd>split<CR>")
  map("n", "sk", "<cmd>set nosplitbelow<CR><cmd>split<CR>")

  map("n", "<leader>l", "<C-w>l")
  map("n", "<leader>h", "<C-w>h")
  map("n", "<leader>j", "<C-w>j")
  map("n", "<leader>k", "<C-w>k")
end
