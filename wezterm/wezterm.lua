local wezterm = require 'wezterm'
local custom = wezterm.color.get_builtin_schemes()["Gruvbox Hard"]
-- custom.background = "#11111b"
-- custom.tab_bar.background = "#040404"
-- custom.tab_bar.inactive_tab.bg_color = "#0f0f0f"
-- custom.tab_bar.new_tab.bg_color = "#080808"

return {
    font = wezterm.font 'MesloLGLDZ NFM',
    font_size = 14,
    color_scheme = 'Gruvbox dark, hard (base16)',
    window_decorations = "RESIZE"
}
