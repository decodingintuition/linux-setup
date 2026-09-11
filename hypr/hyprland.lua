-- Hyprland Lua configuration.
-- Original configuration and scripts are saved under backups/before-lua-*.

local terminal = "wezterm"
local fileManager = "nemo"
local menu = "hyprlauncher"
local mainMod = "ALT"

-- Displays and workspace placement.
hl.monitor({ output = "DP-1", mode = "2560x1440@144", position = "0x0", scale = 1 })
hl.monitor({ output = "DP-2", mode = "2560x1440@144", position = "2560x0", scale = 1 })
for i = 1, 10 do
    hl.workspace_rule({
        workspace = tostring(i),
        monitor = i <= 5 and "DP-1" or "DP-2",
        default = i == 1 or i == 10,
    })
end

-- Environment and startup applications.
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("GTK_THEME", "Adwaita-dark")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.on("hyprland.start", function()
    hl.exec_cmd("nm-applet &")
end)
-- Run at startup and on each reload, matching the previous exec entries.
hl.exec_cmd("pkill hyprpaper; hyprpaper &")
hl.exec_cmd("~/.config/hypr/scripts/set-wallpaper.sh")
hl.exec_cmd("pkill waybar; waybar &")

-- Appearance, layout, and input.
hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 20,
        border_size = 2,
        col = {
            active_border = "rgba(76c395ee)",
            inactive_border = "rgba(7e9792aa)",
        },
        resize_on_border = false,
        allow_tearing = false,
        layout = "dwindle",
    },
    decoration = {
        rounding = 10,
        rounding_power = 2,
        active_opacity = 1.0,
        inactive_opacity = 1.0,
        shadow = {
            enabled = true,
            range = 4,
            render_power = 3,
            color = "rgba(1a1a1aee)",
        },
        blur = {
            enabled = true,
            size = 3,
            passes = 1,
            vibrancy = 0.1696,
        },
    },
    animations = { enabled = true },
    dwindle = { preserve_split = true },
    master = { new_status = "master", orientation = "left" },
    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
    },
    input = {
        kb_layout = "us",
        kb_variant = "",
        kb_model = "",
        kb_options = "",
        kb_rules = "",
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = { natural_scroll = false },
    },
})

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.device({ name = "epic-mouse-v1", sensitivity = -0.5 })
hl.device({ name = "wacom-intuos-bt-m-pen", output = "DP-1" })
hl.device({ name = "weylus-stylus", output = "DP-1" })

-- Animation curves and timings.
hl.curve("easeOutQuint", { type = "bezier", points = { {0.23, 1}, {0.32, 1} } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1} } })
hl.curve("linear", { type = "bezier", points = { {0, 0}, {1, 1} } })
hl.curve("almostLinear", { type = "bezier", points = { {0.5, 0.5}, {0.75, 1} } })
hl.curve("quick", { type = "bezier", points = { {0.15, 0}, {0.1, 1} } })
hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 4.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesIn", enabled = true, speed = 1.21, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesOut", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "zoomFactor", enabled = true, speed = 7, bezier = "quick" })

-- Window rules.
hl.window_rule({
    name = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})
hl.window_rule({
    name = "fix-xwayland-drags",
    match = {
        class = "^$", title = "^$", xwayland = true,
        float = true, fullscreen = false, pin = false,
    },
    no_focus = true,
})
hl.window_rule({
    name = "move-hyprland-run",
    match = { class = "hyprland-run" },
    move = { 20, "monitor_h-120" },
    float = true,
})
-- Global handle used by cycle-layout.sh through hyprctl eval.
floatAllRule = hl.window_rule({
    name = "float-all",
    enabled = false,
    match = { class = ".*" },
    float = true,
})

-- Keybindings retain Alt as the main modifier.
-- Alt+F toggles fullscreen and Alt+Shift+F toggles maximize.
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + X", hl.dsp.window.close())
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd("hyprlock"))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("pavucontrol"))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd("blueman-manager"))
hl.bind(mainMod .. " + semicolon", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + Y", hl.dsp.exec_cmd("grimblast copy area"))
hl.bind(mainMod .. " + SHIFT + Y", hl.dsp.exec_cmd("grimblast save area ~/Downloads/$(date +%Y%m%d-%H%M%S).png"))
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd("hyprpicker -a"))
hl.bind(mainMod .. " + SHIFT + T", hl.dsp.layout("togglesplit"))
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd("~/.config/hypr/scripts/cycle-layout.sh"))
hl.bind(mainMod .. " + Tab", hl.dsp.layout("cyclenext"))
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen())
hl.bind(mainMod .. " + SHIFT + F", hl.dsp.window.fullscreen({ mode = "maximized" }))
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up", hl.dsp.exec_cmd("~/.config/hypr/scripts/focus.sh u"))
hl.bind(mainMod .. " + down", hl.dsp.exec_cmd("~/.config/hypr/scripts/focus.sh d"))
hl.bind(mainMod .. " + h", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + l", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + k", hl.dsp.exec_cmd("~/.config/hypr/scripts/focus.sh u"))
hl.bind(mainMod .. " + j", hl.dsp.exec_cmd("~/.config/hypr/scripts/focus.sh d"))
hl.bind(mainMod .. " + 1", hl.dsp.focus({ workspace = "1" }))
hl.bind(mainMod .. " + 2", hl.dsp.focus({ workspace = "2" }))
hl.bind(mainMod .. " + 3", hl.dsp.focus({ workspace = "3" }))
hl.bind(mainMod .. " + 4", hl.dsp.focus({ workspace = "4" }))
hl.bind(mainMod .. " + 5", hl.dsp.focus({ workspace = "5" }))
hl.bind(mainMod .. " + 6", hl.dsp.focus({ workspace = "6" }))
hl.bind(mainMod .. " + 7", hl.dsp.focus({ workspace = "7" }))
hl.bind(mainMod .. " + 8", hl.dsp.focus({ workspace = "8" }))
hl.bind(mainMod .. " + 9", hl.dsp.focus({ workspace = "9" }))
hl.bind(mainMod .. " + 0", hl.dsp.focus({ workspace = "10" }))
hl.bind(mainMod .. " + SHIFT + 1", hl.dsp.window.move({ workspace = "1" }))
hl.bind(mainMod .. " + SHIFT + 2", hl.dsp.window.move({ workspace = "2" }))
hl.bind(mainMod .. " + SHIFT + 3", hl.dsp.window.move({ workspace = "3" }))
hl.bind(mainMod .. " + SHIFT + 4", hl.dsp.window.move({ workspace = "4" }))
hl.bind(mainMod .. " + SHIFT + 5", hl.dsp.window.move({ workspace = "5" }))
hl.bind(mainMod .. " + SHIFT + 6", hl.dsp.window.move({ workspace = "6" }))
hl.bind(mainMod .. " + SHIFT + 7", hl.dsp.window.move({ workspace = "7" }))
hl.bind(mainMod .. " + SHIFT + 8", hl.dsp.window.move({ workspace = "8" }))
hl.bind(mainMod .. " + SHIFT + 9", hl.dsp.window.move({ workspace = "9" }))
hl.bind(mainMod .. " + SHIFT + 0", hl.dsp.window.move({ workspace = "10" }))
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag())
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize())
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { repeating = true, locked = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { repeating = true, locked = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { repeating = true, locked = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { repeating = true, locked = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { repeating = true, locked = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { repeating = true, locked = true })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })
hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd("pkill waybar; waybar &"))
hl.bind(mainMod .. " + CTRL + B", hl.dsp.exec_cmd("pkill -SIGUSR1 waybar"))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("hyprctl reload; rm -f \"$XDG_RUNTIME_DIR\"/hypr-layout-mode"))
