return {
  'ibhagwan/fzf-lua',
  -- optional for icon support
  dependencies = { 'nvim-tree/nvim-web-devicons' },
  -- or if using mini.icons/mini.nvim
  -- dependencies = { "nvim-mini/mini.icons" },
  ---@module "fzf-lua"
  ---@type fzf-lua.Config|{}
  ---@diagnostic disable: missing-fields
  opts = {},
  ---@diagnostic enable: missing-fields
  vim.keymap.set('n', '<leader>p', '<cmd>FzfLua files<CR>'),
  vim.keymap.set('n', '<leader>fg', '<cmd>FzfLua live_grep<CR>'),
  vim.keymap.set('n', '<leader>fm', '<cmd>FzfLua marks<CR>'),
}
