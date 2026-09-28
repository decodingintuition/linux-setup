#!/usr/bin/env bash
# Toggle gamma 3.0. Disconnecting wl-gammactl restores the original gamma tables.
set -euo pipefail

runtime_dir="${XDG_RUNTIME_DIR:?XDG_RUNTIME_DIR is required}"
exec 9>"$runtime_dir/hypr-gamma-toggle.lock"
flock 9

if pkill -u "$UID" -x wl-gammactl; then
    pidwait -u "$UID" -x wl-gammactl || true
    # Hyprland resets gamma on disconnect without scheduling a redraw.
    hyprctl -r monitors >/dev/null
    exit 0
fi

# The background client must not inherit the toggle lock.
nohup wl-gammactl -g 3 </dev/null >"$runtime_dir/hypr-gamma-toggle.log" 2>&1 9>&- &
