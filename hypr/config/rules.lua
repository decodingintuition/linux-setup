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
-- Global floating mode is managed by config.layout.
floatAllRule = hl.window_rule({
    name = "float-all",
    enabled = false,
    match = { class = ".*" },
    float = true,
})
