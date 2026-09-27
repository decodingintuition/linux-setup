-- Keep layout selection across reloads, but start each session in monocle.
desktopLayout = desktopLayout or { tiled = "monocle", floating = false, wasFloating = {} }
local layout = desktopLayout

local function apply_tiled()
    hl.config({ general = { layout = layout.tiled == "main" and "master" or "monocle" } })
end

local function leave_floating()
    layout.floating = false
    floatAllRule:set_enabled(false)
    apply_tiled()
    for _, window in ipairs(hl.get_windows()) do
        if window.floating and not layout.wasFloating[window.address] then
            hl.dispatch(hl.dsp.window.float({ action = "unset", window = window }))
        end
    end
    layout.wasFloating = {}
end

function layout.toggle_floating()
    if layout.floating then
        leave_floating()
        return
    end
    layout.wasFloating = {}
    local windows = hl.get_windows()
    for _, window in ipairs(windows) do
        if window.floating then
            layout.wasFloating[window.address] = true
        end
    end
    layout.floating = true
    floatAllRule:set_enabled(true)
    for _, window in ipairs(windows) do
        if not window.floating then
            hl.dispatch(hl.dsp.window.float({ action = "set", window = window }))
        end
    end
end

function layout.cycle()
    if layout.floating then
        leave_floating()
    end
    layout.tiled = layout.tiled == "monocle" and "main" or "monocle"
    apply_tiled()
end

apply_tiled()
floatAllRule:set_enabled(layout.floating)
