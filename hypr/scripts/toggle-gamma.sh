#!/usr/bin/env bash
# Toggle between neutral gamma and the value selected in Waybar.
set -euo pipefail
exec python3 "${XDG_CONFIG_HOME:-$HOME/.config}/waybar/scripts/gamma.py" toggle
