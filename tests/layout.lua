local windows = {
    { address = "tiled", floating = false },
    { address = "dialog", floating = true },
}
local selected, floating_rule
hl = {
    config = function(config) selected = config.general.layout end,
    get_windows = function() return windows end,
    dsp = { window = { float = function(options)
        return function() options.window.floating = options.action == "set" end
    end } },
    dispatch = function(action) action() end,
}
floatAllRule = {
    set_enabled = function(_, enabled) floating_rule = enabled end,
}
local function reload()
    dofile("hypr/config/layout.lua")
end
reload()
assert(selected == "monocle" and not floating_rule, "new sessions start in monocle")

desktopLayout.cycle()
assert(selected == "master" and not floating_rule, "cycle selects main")
reload()
assert(selected == "master", "main survives configuration reload")
desktopLayout.toggle_floating()
assert(floating_rule and windows[1].floating, "floating applies to tiled windows")
assert(desktopLayout.tiled == "main", "floating remembers main")
windows[3] = { address = "new", floating = true }
reload()
assert(floating_rule and desktopLayout.floating, "floating survives reload")
desktopLayout.toggle_floating()
assert(selected == "master" and not floating_rule, "floating returns to main")
assert(not windows[1].floating and not windows[3].floating, "old and new tiled windows return")
assert(windows[2].floating, "existing floating windows remain floating")

desktopLayout.cycle()
assert(selected == "monocle", "cycle returns to monocle")
desktopLayout.toggle_floating()
desktopLayout.toggle_floating()
assert(selected == "monocle" and not floating_rule, "floating returns to monocle")
desktopLayout.toggle_floating()
desktopLayout.cycle()
assert(selected == "master" and not floating_rule, "cycle while floating selects next tiled layout")

windows = {}
desktopLayout.toggle_floating()
desktopLayout.toggle_floating()
assert(selected == "master" and not floating_rule, "empty sessions support toggling")
desktopLayout = nil
reload()
assert(selected == "monocle", "a new session resets to monocle")
print("Layout transitions, reload persistence, and floating-window restoration passed")
