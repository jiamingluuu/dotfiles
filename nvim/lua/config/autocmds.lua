vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = { "py", "c", "cpp", "rust" },
  callback = function()
    vim.b.autoformat = false
  end,
})
