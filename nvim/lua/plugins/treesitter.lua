return {
  'nvim-treesitter/nvim-treesitter',
  lazy = false,
  build = ':TSUpdate',
  opts = {
    ensure_installed = { 'bash', 'c', 'cpp', 'python', 'rust' },
    indent = { enable = true },
    context_commentstring = {
      enable = true,
      enable_autocmd = false,
    },
  },
  -- init = function()
  --   vim.api.nvim_create_autocmd('FileType', {
  --     pattern = { 'markdown' },
  --     callback = function(args)
  --       local ok, parser = pcall(vim.treesitter.get_parser, args.buf)
  --       if not ok or not parser then return end
  --
  --       local has_broken_child = false
  --       for _, child in ipairs(parser:children() or {}) do
  --         local lang = child:lang()
  --         if lang == 'markdown_inline' then
  --           has_broken_child = true
  --           break
  --         end
  --       end
  --
  --       if has_broken_child then vim.treesitter.stop(args.buf) end
  --     end,
  --     desc = 'Avoid markdown_inline Treesitter startup crash on Neovim 0.12.2',
  --   })
  -- end,
}
