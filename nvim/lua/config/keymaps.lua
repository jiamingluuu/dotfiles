vim.keymap.set('t', '<Esc><Esc>', '<C-\\><C-n>', { desc = 'Exit terminal mode' })

vim.keymap.set('n', '<C-h>', '<C-w><C-h>', { desc = 'Move focus to the left window' })
vim.keymap.set('n', '<C-l>', '<C-w><C-l>', { desc = 'Move focus to the right window' })
vim.keymap.set('n', '<C-j>', '<C-w><C-j>', { desc = 'Move focus to the lower window' })
vim.keymap.set('n', '<C-k>', '<C-w><C-k>', { desc = 'Move focus to the upper window' })
-- vim.keymap.set('n', 'sh', '<cmd>split<CR>')
-- vim.keymap.set('n', 'sv', '<cmd>vsplit<CR>')
vim.keymap.set('n', 'L', '$')
vim.keymap.set('n', 'H', '0')

vim.keymap.set('v', 'H', '0')
vim.keymap.set('v', 'J', '5j')
vim.keymap.set('v', 'K', '5k')
vim.keymap.set('v', 'L', '$')

vim.keymap.set('n', 'Q', '<cmd>q<CR>')
vim.keymap.set('n', 'S', '<cmd>w<CR>')

vim.keymap.set('n', '<leader><CR>', '<cmd>nohl<CR>')
vim.keymap.set('n', '<leader>sc', '<cmd>set spell!<CR>')
vim.keymap.set('n', '<leader>sv', function()
  local variable = vim.fn.expand '<cword>'
  if variable == '' then return end

  vim.fn.setreg('/', '\\<' .. vim.fn.escape(variable, '\\/.*$^~[]') .. '\\>')
  vim.opt.hlsearch = true
  vim.cmd 'normal! nzz'
end, { desc = '[S]earch [V]ariable under cursor' })

vim.keymap.set('n', 'tn', '<cmd>tabe<CR>')
vim.keymap.set('n', 'th', '<cmd>-tabnext<CR>')
vim.keymap.set('n', 'tl', '<cmd>+tabnext<CR>')

vim.keymap.set('n', 'sh', '<cmd>set nosplitright<CR><cmd>vsplit<CR>')
vim.keymap.set('n', 'sl', '<cmd>set splitright<CR><cmd>vsplit<CR>')
vim.keymap.set('n', 'sj', '<cmd>set splitbelow<CR><cmd>split<CR>')
vim.keymap.set('n', 'sk', '<cmd>set nosplitbelow<CR><cmd>split<CR>')

vim.keymap.set('n', '<leader>l', '<C-w>l')
vim.keymap.set('n', '<leader>h', '<C-w>h')
vim.keymap.set('n', '<leader>j', '<C-w>j')
vim.keymap.set('n', '<leader>k', '<C-w>k')

vim.keymap.set('n', 'gD', '<cmd>lua vim.lsp.buf.declaration()<CR>', { noremap = true, silent = true })
vim.keymap.set('n', 'gd', '<cmd>lua vim.lsp.buf.definition()<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>i', '<cmd>lua vim.diagnostic.open_float()<CR>', { noremap = true, silent = true })
