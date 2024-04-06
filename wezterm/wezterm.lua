local wezterm = require("wezterm")

local custom = wezterm.color.get_builtin_schemes()["Catppuccin Mocha"]
custom.background = "#000000"
custom.tab_bar.background = "#040404"
custom.tab_bar.inactive_tab.bg_color = "#0f0f0f"
custom.tab_bar.new_tab.bg_color = "#080808"

return {
	font = wezterm.font("MesloLGMDZ Nerd Font"),
	font_size = 12,
	-- color_scheme = "Gruvbox dark, hard (base16)",
	color_schemes = {
		["OLEDppuccin"] = custom,
	},
	color_scheme = "OLEDppuccin",
	window_decorations = "RESIZE",
	window_frame = {
		font_size = 9,
	},
}
