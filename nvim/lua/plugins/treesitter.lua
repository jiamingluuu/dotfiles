local parsers = {
  'bash',
  'c',
  'cpp',
  'markdown',
  'markdown_inline',
  'python',
  'rust',
  'typst',
}

return {
  'nvim-treesitter/nvim-treesitter',
  lazy = false,
  build = ':TSUpdate',
  config = function()
    require('nvim-treesitter').install(parsers)

    vim.api.nvim_create_autocmd('FileType', {
      group = vim.api.nvim_create_augroup('treesitter-start', { clear = true }),
      pattern = { 'c', 'cpp', 'python', 'markdown', 'rust', 'typst' },
      callback = function(args)
        pcall(vim.treesitter.start, args.buf)
        vim.bo[args.buf].indentexpr = 'v:lua.require"nvim-treesitter".indentexpr()'
      end,
      desc = 'Start Treesitter highlighting and indentation',
    })
  end,
}
