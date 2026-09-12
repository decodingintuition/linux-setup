-- Keyboard, pointer, gestures, and devices.
hl.config({
    input = {
        kb_layout = "us",
        kb_file = "~/.config/hypr/keymap-mod3.xkb",
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
