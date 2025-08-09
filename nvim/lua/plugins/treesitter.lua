return {
  "nvim-treesitter/nvim-treesitter",
  opts = {
    ensure_installed = { "bash", "c", "cpp", "python", "rust" },
    indent = { enable = true, },
    context_commentstring = {
      enable = true,
      enable_autocmd = false,
    },
  }
}
