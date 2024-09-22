vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = { "c", "cpp", "rust" },
  callback = function()
    vim.b.autoformat = false
  end,
})
