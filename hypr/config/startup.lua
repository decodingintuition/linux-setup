-- Environment and startup applications.
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("GTK_THEME", "Adwaita-dark")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.on("hyprland.start", function()
    hl.exec_cmd("nm-applet &")
    hl.exec_cmd("waybar &")
end)
-- Run at startup and on each reload, matching the previous exec entries.
hl.exec_cmd("pkill hyprpaper; hyprpaper &")
hl.exec_cmd("~/.config/hypr/scripts/set-wallpaper.sh")
