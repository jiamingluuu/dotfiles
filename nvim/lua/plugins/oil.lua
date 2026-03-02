return {
  'https://github.com/stevearc/oil.nvim',

  opts = {
    default_file_explorer = true,
    detail = false,
    keymaps = {
      ['<C-h>'] = false,
      ['<C-l>'] = false,
      ['<C-k>'] = false,
      ['<C-j>'] = false,
      ['<C-r>'] = 'actions.refresh',
      ['<leader>y'] = 'actions.yank_entry',
      ['g.'] = false,
      ['zh'] = 'actions.toggle_hidden',
      ['\\'] = { 'actions.select', opts = { horizontal = true } },
      ['|'] = { 'actions.select', opts = { vertical = true } },
      ['-'] = 'actions.close',
      ['<leader>e'] = 'actions.close',
      ['<BS>'] = 'actions.parent',
      ['gd'] = {
        desc = 'Toggle file detail view',
        callback = function()
          detail = not detail
          if detail then
            require('oil').set_columns { 'icon', 'permissions', 'size', 'mtime' }
          else
            require('oil').set_columns { 'icon' }
          end
        end,
      },
    },
    win_options = {
      wrap = false,
      signcolumn = 'no',
      cursorcolumn = false,
      foldcolumn = '0',
      spell = false,
      list = false,
      conceallevel = 3,
      concealcursor = 'nvic',
    },
  },
  vim.keymap.set('n', '-', ':Oil<CR>'),
}
