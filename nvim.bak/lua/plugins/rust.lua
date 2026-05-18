return {
  "mrcjkb/rustaceanvim",
  ft = "rust",
  config = function()
    vim.g.rustaceanvim = {
      server = {
        on_attach = function(client, bufnr)
          if client.server_capabilities.inlayHintProvider then
            vim.lsp.inlay_hint.enable(true, { bufnr = bufnr })
          end
        end,
        settings = {
          ["rust-analyzer"] = {
            inlayHints = {
              parameterHints = { enable = false },
              typeHints = { enable = false }, -- the “return type” style hints you want
              chainingHints = { enable = true },
              closureReturnTypeHints = { enable = "never" }, -- "never" | "always" | "with_block"
              lifetimeElisionHints = { enable = "skip_trivial" },
              expressionAdjustmentHints = { enable = "never" }, -- casts/refs/derefs
              implicitDrops = { enable = false },
            },
            reborrowHints = { enable = "always" },
          },
        },
      },
    }
  end,
}
