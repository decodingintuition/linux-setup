#!/usr/bin/env bash
# Print the current GLOBAL layout mode for the waybar custom/layout module.
# Floating is tracked by cycle-layout.sh in a state file; otherwise read live from
# general:layout. Glyphs are Material Design Icons from the nerd font (verified
# present in FantasqueSansM Nerd Font Mono).

set -euo pipefail

state="${XDG_RUNTIME_DIR:-/tmp}/hypr-layout-mode"

mode=$(cat "$state" 2>/dev/null || true)
case "$mode" in
    monocle | floating | main) ;;
    master) mode=main ;; # Hyprland's internal name
    *)
        mode=$(hyprctl getoption general:layout -j | jq -r '.str')
        [[ $mode == master ]] && mode=main
        ;;
esac

case "$mode" in
    floating) echo "󰖲 floating" ;;
    main) echo "󰕱 main" ;;
    monocle) echo "󰖯 monocle" ;;
    dwindle) echo "󰕰 dwindle" ;;
    scrolling) echo "󰗅 scrolling" ;;
    *) echo "$mode" ;;
esac
