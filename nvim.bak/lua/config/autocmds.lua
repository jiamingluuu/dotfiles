vim.api.nvim_create_autocmd({ "FileType" }, {
  pattern = { "py", "c", "cpp", "cc", "h", "ml", "rs" },
  callback = function()
    vim.b.autoformat = false
  end,
})

local function augroup(name)
  return vim.api.nvim_create_augroup("custom_" .. name, { clear = true })
end

vim.api.nvim_create_autocmd({ "FileType" }, {
  group = augroup("rust_disable_single_quote_pairs"),
  pattern = "rust",
  callback = function()
    vim.keymap.set("i", "'", "'", { buffer = 0 })
    vim.keymap.set("i", "`", "`", { buffer = 0 })
  end,
})

vim.api.nvim_create_autocmd({ "FileType" }, {
  group = augroup("ocaml_disable_single_quote_pairs"),
  pattern = "ocaml",
  callback = function()
    vim.keymap.set("i", "'", "'", { buffer = 0 })
    vim.keymap.set("i", "`", "`", { buffer = 0 })
  end,
})
