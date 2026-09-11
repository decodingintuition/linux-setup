#!/usr/bin/env bash
set -euo pipefail

config_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_config="$config_dir/default.conf"
target=/etc/keyd/default.conf

if [[ ! -f "$source_config" ]]; then
    printf 'Missing configuration file: %s\n' "$source_config" >&2
    exit 1
fi

if [[ -e "$target" || -L "$target" ]]; then
    if [[ ! -L "$target" || "$(readlink -f -- "$target")" != "$source_config" ]]; then
        printf 'Existing configuration must be moved aside before installation: %s\n' "$target" >&2
        exit 1
    fi
fi

sudo pacman -S --needed --noconfirm keyd

if [[ ! -L "$target" ]]; then
    sudo mkdir -p -- /etc/keyd
    sudo ln -s -- "$source_config" "$target"
fi

sudo systemctl enable --now keyd
sudo keyd reload

printf 'Done. Edit %s, then run: sudo keyd reload\n' "$source_config"
