-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here
-- Disable autoformat for lua files
vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = { "py", "c", "cpp" },
  callback = function()
    vim.b.autoformat = false
  end,
})
vim.api.nvim_create_autocmd({ "CursorHold" }, {
  callback = function()
    if vim.lsp.buf.server_ready() then
      vim.diagnostic.open_float()
    end
  end,
})
