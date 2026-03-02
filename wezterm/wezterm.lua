local wezterm = require("wezterm")

return {
	audible_bell = "Disabled",
	-- color_scheme = "Gruvbox Dark (Gogh)",
	-- colors = {
	-- 	tab_bar = {
	-- 		background = "rgba(16%, 16%, 16%, 90%)",
	-- 		active_tab = {
	-- 			bg_color = "#b8bb26",
	-- 			fg_color = "rgba(16%, 16%, 16%, 0%)",
	-- 			intensity = "Bold",
	-- 		},
	-- 		inactive_tab = {
	-- 			fg_color = "#b8bb26",
	-- 			bg_color = "rgba(16%, 16%, 16%, 90%)",
	-- 			intensity = "Normal",
	-- 		},
	-- 		inactive_tab_hover = {
	-- 			fg_color = "#cba6f7",
	-- 			bg_color = "rgba(27%, 28%, 35%, 90%)",
	-- 			intensity = "Bold",
	-- 		},
	-- 		new_tab = {
	-- 			fg_color = "#808080",
	-- 			bg_color = "#1e1e2e",
	-- 		},
	-- 	},
	-- },

	color_scheme = "Catppuccin Mocha",
	colors = {
		tab_bar = {
			background = "rgba(12%, 12%, 18%, 90%)",
			active_tab = {
				bg_color = "#cba6f7",
				fg_color = "rgba(12%, 12%, 18%, 0%)",
				intensity = "Bold",
			},
			inactive_tab = {
				fg_color = "#cba6f7",
				bg_color = "rgba(12%, 12%, 18%, 90%)",
				intensity = "Normal",
			},
			inactive_tab_hover = {
				fg_color = "#cba6f7",
				bg_color = "rgba(27%, 28%, 35%, 90%)",
				intensity = "Bold",
			},
			new_tab = {
				fg_color = "#808080",
				bg_color = "#1e1e2e",
			},
		},
	},

	font = wezterm.font("MesloLGLDZ NFM"),
	font_size = 14,
	enable_tab_bar = true,
	use_fancy_tab_bar = false,
	hide_tab_bar_if_only_one_tab = true,
	show_new_tab_button_in_tab_bar = false,
	window_decorations = "RESIZE",
}
