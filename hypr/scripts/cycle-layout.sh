#!/usr/bin/env bash
# Switch tiled layouts or toggle global floating mode.
set -euo pipefail

case "${1:-cycle}" in
    cycle) action=cycle ;;
    toggle-floating) action=toggle_floating ;;
    *) printf 'Usage: %s [cycle|toggle-floating]\n' "$0" >&2; exit 2 ;;
esac

result=$(hyprctl eval "desktopLayout.$action()")
if [[ $result != ok ]]; then
    printf '%s\n' "$result" >&2
    exit 1
fi
mode=$(hyprctl repl 'return desktopLayout.floating and "floating" or desktopLayout.tiled')
pkill -RTMIN+8 -u "$(id -u)" -x waybar 2>/dev/null || true
hyprctl notify -1 1200 0 "layout: $mode" > /dev/null
