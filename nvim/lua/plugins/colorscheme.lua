return {
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
  -- {
  --   "catppuccin/nvim",
  --   name = "catppuccin",
  --   priority = 1000,
  --   opts = {
  --     flavour = "latte",
  --     term_colors = true,
  --     transparent_background = false,
  --     styles = {
  --       comments = { "italic" },
  --       conditionals = {},
  --       loops = {},
  --       functions = {},
  --       keywords = {},
  --       strings = {},
  --       variables = { "italic" },
  --       numbers = {},
  --       booleans = { "italic" },
  --       properties = {},
  --       types = {},
  --     },
  --     color_overrides = {
  -- 		mocha = {
  -- 			base = "#111111",
  -- 			mantle = "#161616",
  -- 			crust = "#181818",
  -- 		},
  -- 	},
  --     integrations = {
  --       cmp = true,
  --       gitsigns = true,
  --       nvimtree = true,
  --       treesitter = true,
  --       notify = false,
  --       mini = {
  --         enabled = true,
  --         indentscope_color = "",
  --       },
  --     },
  --   },
  -- },
  { "Mofiqul/vscode.nvim" },
  { "projekt0n/github-nvim-theme" },
  {
    "LazyVim/LazyVim",
    opts = {
      -- colorscheme = "gruvbox",
      colorscheme = "catppuccin",
      -- colorscheme = "vscode",
      -- colorscheme = "github_dark_default",
    },
  },
}
