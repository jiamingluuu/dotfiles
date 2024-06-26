return {
  "neovim/nvim-lspconfig",
  init = function()
    local keys = require("lazyvim.plugins.lsp.keymaps").get()
    keys[#keys + 1] = { "K", false }
  end,
  opts = {
    servers = {
      pylsp = {
        settings = {
          pylsp = {
            plugins = {
              pyflakes = { enabled = false },
            },
          },
        },
      },
    },
    diagnostics = {
      virtual_text = false,
    },
  },
}
