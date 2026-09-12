#!/usr/bin/env bash
# Cycle the GLOBAL layout scheme: monocle -> floating -> main -> monocle ...
# Applies to every workspace at once (general:layout).
#
#   monocle   windows stacked one on top of the other (native layout)
#   floating  nothing tiles; windows opened while in this mode float too
#   main      main window + stack (Hyprland calls this layout "master")
#
# general:layout has no "floating" value, so that mode is the `float-all`
# window rule (declared disabled in config/rules.lua) flipped on plus a setfloating
# pass over existing windows. Special-category values can't be read back via
# `hyprctl getoption`, so the mode is tracked in a state file; every press
# re-asserts the whole target state, so a stale file costs one extra keypress.

set -euo pipefail

state="${XDG_RUNTIME_DIR:-/tmp}/hypr-layout-mode"

current=$(cat "$state" 2>/dev/null || true)
case "$current" in
    monocle | floating | main) ;;
    master) current=main ;; # Migrate old state and Hyprland's internal name
    *)
        current=$(hyprctl getoption general:layout -j | jq -r '.str')
        [[ $current == master ]] && current=main
        ;;
esac

case "$current" in
    monocle) next=floating ;;
    floating) next=main ;;
    *) next=monocle ;; # main / dwindle / scrolling -> head of the cycle
esac

mapfile -t addrs < <(hyprctl clients -j | jq -r '.[] | select(.mapped) | .address')

batch=()
if [[ $next == floating ]]; then
    batch+=("eval floatAllRule:set_enabled(true)")
    for a in "${addrs[@]}"; do batch+=("dispatch setfloating address:$a"); done
else
    batch+=("eval floatAllRule:set_enabled(false)")
    hyprland_layout=$next
    [[ $next == main ]] && hyprland_layout=master
    batch+=("eval hl.config({general = {layout = '$hyprland_layout'}})")
    # Only re-tile on the way out of floating, so windows floated on purpose
    # (pavucontrol, hyprland-run) survive a monocle <-> main cycle.
    if [[ $current == floating ]]; then
        for a in "${addrs[@]}"; do batch+=("dispatch settiled address:$a"); done
    fi
fi

# hyprctl --batch separates commands with ';'. Join explicitly: a prefix
# assignment (IFS=';' hyprctl ...) would not apply to "${batch[*]}" itself.
joined=$(printf '%s ; ' "${batch[@]}")
hyprctl --batch "${joined% ; }" > /dev/null

printf '%s\n' "$next" > "$state"
pkill -RTMIN+8 waybar 2>/dev/null || true
hyprctl notify -1 1200 0 "layout: $next" > /dev/null
