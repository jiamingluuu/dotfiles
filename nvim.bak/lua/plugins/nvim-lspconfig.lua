return {
  "neovim/nvim-lspconfig",
  opts = {
    inlay_hints = { enabled = false },
    servers = {
      rust_analyzer = {
        mason = false,
        cmd = { vim.fn.expand("/usr/bin/rust-analyzer") },
      },
      pylsp = {
        settings = {
          pylsp = {
            plugins = {
              pyflakes = { enabled = false },
              pycodestyle = {
                ignore = { "E501" },
              },
            },
          },
        },
      },
    },
  },
}
