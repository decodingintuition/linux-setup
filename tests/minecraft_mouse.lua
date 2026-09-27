local active, press, release
local sent = {}
local function dispatcher()
    return setmetatable({}, {
        __index = function() return dispatcher() end,
        __call = function() return function() return { ok = true } end end,
    })
end
hl = {
    dsp = dispatcher(),
    get_active_window = function() return active end,
    dispatch = function(action) return action() end,
    bind = function(key, action, options)
        if key ~= "mouse:275" then return end
        assert(options.auto_consuming, "unhandled clicks must pass through")
        if options.release then
            assert(options.ignore_mods, "modifier changes must not prevent release")
            release = action
        else
            press = action
        end
    end,
}
hl.dsp.send_key_state = function(options)
    return function()
        assert(options.key == "F3" and options.mods == "")
        table.insert(sent, options)
        return { ok = true }
    end
end
dofile("hypr/config/keybindings.lua")
assert(press and release, "both mouse edges must be handled")

for _, class in ipairs({ "Minecraft* 26.1.1", "minecraft", "Minecraft 1.21" }) do
    active = { class = class, mapped = true }
    local game = active
    sent = {}
    assert(press().ok, "Minecraft must consume the mouse press")
    assert(#sent == 1 and sent[1].state == "down", "F3 must stay down until mouse release")
    assert(sent[1].window == game, "F3 press must target the game")
    active = { class = "zen" }
    assert(release().ok, "the matching release stays consumed after a focus change")
    assert(#sent == 2 and sent[2].state == "up", "mouse release must release F3")
    assert(sent[2].window == game, "F3 release must target the original game")
    assert(not release().ok and #sent == 2, "duplicate releases must not resend F3")
end

for _, class in ipairs({ "org.prismlauncher.PrismLauncher", "zen", "wezterm" }) do
    active = { class = class }
    sent = {}
    assert(not press().ok, "other apps must retain mouse presses")
    active = { class = "Minecraft* 26.1.1" }
    assert(not release().ok, "a passed-through press must retain its release")
    assert(#sent == 0, "other apps must not receive F3")
end

active = nil
sent = {}
assert(not press().ok and not release().ok and #sent == 0, "no focused window is safe")

active = { class = "Minecraft", mapped = true }
sent = {}
assert(press().ok)
active.mapped = false
assert(release().ok and #sent == 1, "closed games must not receive key events")
print("Minecraft mouse binding checks passed")
