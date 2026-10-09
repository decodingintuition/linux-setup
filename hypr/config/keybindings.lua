local terminal = "wezterm"
local fileManager = "nemo"
local menu = "hyprlauncher"
-- Physical Right Super emits Right Alt here, mapped to Mod3 by the XKB keymap.
local mainMod = "MOD3"

-- Side buttons send F3 and F5 in legacy and native Wayland Minecraft windows.
local function bindMinecraftMouseKey(button, key)
    local minecraftMouseWindow
    hl.bind(button, function()
        local window = hl.get_active_window()
        local class = window and window.class:lower() or ""
        if not class:match("^minecraft") and class ~= "com.mojang.minecraft" then
            minecraftMouseWindow = nil
            return { ok = false }
        end
        local result = hl.dispatch(hl.dsp.send_key_state({ mods = "", key = key, state = "down", window = window }))
        minecraftMouseWindow = result.ok and window or nil
        return result
    end, { auto_consuming = true })
    hl.bind(button, function()
        local window = minecraftMouseWindow
        minecraftMouseWindow = nil
        if not window then return { ok = false } end
        if window.mapped then
            hl.dispatch(hl.dsp.send_key_state({ mods = "", key = key, state = "up", window = window }))
        end
        return { ok = true }
    end, { release = true, auto_consuming = true, ignore_mods = true })
end
bindMinecraftMouseKey("mouse:275", "F3")
bindMinecraftMouseKey("mouse:276", "F5")

-- F5 toggles gamma only while ARC Raiders is focused.
local arcGammaPressed = false
hl.bind("F5", function()
    local window = hl.get_active_window()
    if not window or window.class ~= "steam_app_1808500" then
        arcGammaPressed = false
        return { ok = false }
    end
    local result = hl.dispatch(hl.dsp.exec_cmd("~/.config/hypr/scripts/toggle-gamma.sh"))
    arcGammaPressed = result.ok
    return result
end, { auto_consuming = true })
hl.bind("F5", function()
    local consumed = arcGammaPressed
    arcGammaPressed = false
    return { ok = consumed }
end, { release = true, auto_consuming = true, ignore_mods = true })

-- Desktop shortcuts use Right Super through Mod3.
-- Right Super+F toggles fullscreen and Right Super+Shift+F toggles maximize.
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + X", hl.dsp.window.close())
hl.bind(mainMod .. " + SHIFT + X", hl.dsp.window.kill())
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd("hyprlock"))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("pavucontrol"))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd("blueman-manager"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("swaync-client -t -sw"))
hl.bind(mainMod .. " + semicolon", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + Y", hl.dsp.exec_cmd("grimblast --freeze copy area"))
hl.bind(mainMod .. " + SHIFT + Y", hl.dsp.exec_cmd("grimblast --freeze save area ~/Downloads/$(date +%Y%m%d-%H%M%S).png"))
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd("hyprpicker -a"))
hl.bind(mainMod .. " + SHIFT + T", hl.dsp.layout("togglesplit"))
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd("~/.config/hypr/scripts/cycle-layout.sh"))
hl.bind(mainMod .. " + SHIFT + SPACE", hl.dsp.exec_cmd("~/.config/hypr/scripts/cycle-layout.sh toggle-floating"))
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
