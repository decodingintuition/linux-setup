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
