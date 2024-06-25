vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = { "py", "c", "cpp", "rust" },
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
