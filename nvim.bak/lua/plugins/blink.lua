return {
  "saghen/blink.cmp",
  event = { "BufReadPost", "BufNewFile" },
  opts = {
    signature = {
      enabled = true,
    },
    cmdline = {
      completion = {
        menu = {
          auto_show = true,
        },
      },
    },
    sources = {
      default = { "lsp", "snippets", "path" },
    },
  },
}
