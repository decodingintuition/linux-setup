-- Restore native gamma without blocking a compositor reload.
local config = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
hl.dispatch(hl.dsp.exec_cmd("python3 " .. string.format("%q", config .. "/waybar/scripts/gamma.py") .. " status"))
