#!/usr/bin/env bash
# movefocus that understands monocle.
#
# Monocle stacks every window at identical geometry, so Hyprland's directional
# focus has no neighbour to find: CMonocleAlgorithm::moveTargetInDirection() only
# looks for another *monitor* in that direction. With DP-1/DP-2 side by side that
# makes vertical motion dead in monocle, so route it to the stack cycle instead.
# Horizontal motion is passed through untouched, so Right Super+H/L still crosses monitors.
#
# Focus itself is what raises the window: monocle hooks window.active and hides
# every other window (alpha 0 + input block), so whatever we focus comes to front.

set -euo pipefail

dir=${1:?usage: focus.sh <u|d|l|r>}

layout=$(hyprctl activeworkspace -j | jq -r '.tiledLayout')
floating=$(hyprctl activewindow -j | jq -r '.floating // false')

# A floating window is a real position on screen even in monocle mode (and in
# floating mode everything floats), so directional focus is meaningful there.
if [[ $layout == monocle && $floating == false ]]; then
    case "$dir" in
        u) hyprctl dispatch layoutmsg cycleprev > /dev/null ;;
        d) hyprctl dispatch layoutmsg cyclenext > /dev/null ;;
        *) hyprctl dispatch movefocus "$dir" > /dev/null ;;
    esac
else
    hyprctl dispatch movefocus "$dir" > /dev/null
fi
