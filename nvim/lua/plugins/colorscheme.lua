return {
  { "Mofiqul/vscode.nvim" },
  {
    "ellisonleao/gruvbox.nvim",
    opts = {
      styles = {
        comments = { "italic" },
        variables = { "italic" },
        booleans = { "italic" },
        functions = { "italic" },
      },
      color_overrides = {
        functions = { "#f1bf4f" },
      },
    },
  },
  {
    "catppuccin/nvim",
    name = "catppuccin",
    priority = 1000,
    opts = {
      term_colors = true,
      transparent_background = false,
      styles = {
        comments = { "italic" },
        variables = { "italic" },
        booleans = { "italic" },
      },
      color_overrides = {
				mocha = {
					base = "#000000",
					mantle = "#000000",
					crust = "#000000",
				},
			},
      integrations = {
        cmp = true,
        gitsigns = true,
        nvimtree = true,
        treesitter = true,
        notify = false,
        mini = {
          enabled = true,
          indentscope_color = "",
        },
      },
    },
   },
  { "sainnhe/gruvbox-material", },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "gruvbox-material",
      -- colorscheme = "catppuccin",
      -- colorscheme = "vscode",
    },
  },
}
