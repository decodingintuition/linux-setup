#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
target="$config_dir/hypr"
source_dir="$repo_dir/hypr"

if [[ ! -d "$source_dir" ]]; then
    printf 'Missing configuration directory: %s\n' "$source_dir" >&2
    exit 1
fi

mkdir -p -- "$config_dir"
if [[ -L "$target" && "$(readlink -f -- "$target")" == "$source_dir" ]]; then
    printf 'Already linked: %s -> %s\n' "$target" "$source_dir"
    exit 0
fi

if [[ -e "$target" || -L "$target" ]]; then
    printf 'Existing configuration must be moved aside before installation: %s\n' "$target" >&2
    exit 1
fi

ln -s -- "$source_dir" "$target"
printf 'Linked: %s -> %s\n' "$target" "$source_dir"
