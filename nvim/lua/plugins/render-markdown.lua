return {
  'MeanderingProgrammer/render-markdown.nvim',
  dependencies = { 'nvim-treesitter/nvim-treesitter', 'nvim-mini/mini.nvim' },
  opts = {
    code = {
      width = 'block',
      min_width = 80,
      border = 'thin',
      left_pad = 1,
      right_pad = 1,
      position = 'right',
      language_icon = true,
      lanauge_name = true,
    },
    anti_conceal = {
      disabled_modes = { 'n' },
      ignore = {
        head_border = true,
        head_background = true,
      },
    },
  },
}
