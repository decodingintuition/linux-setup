#!/usr/bin/env bash
# Read layout state from the running Hyprland session.
set -euo pipefail

mode=$(hyprctl repl 'return desktopLayout.floating and "floating" or desktopLayout.tiled')
case "$mode" in
    floating) echo "󰖲 floating" ;;
    main) echo "󰕱 main" ;;
    monocle) echo "󰖯 monocle" ;;
    *) echo "$mode" ;;
esac
