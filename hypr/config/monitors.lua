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
