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
