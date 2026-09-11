#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
components=(hypr waybar keyd)

# Check every destination before creating links.
for component in "${components[@]}"; do
    source_dir="$repo_dir/$component"
    target="$config_dir/$component"
    if [[ ! -d "$source_dir" ]]; then
        printf 'Missing configuration directory: %s\n' "$source_dir" >&2
        exit 1
    fi
    if [[ -L "$target" && "$(readlink -f -- "$target")" == "$source_dir" ]]; then
        continue
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        printf 'Existing configuration must be moved aside before installation: %s\n' "$target" >&2
        exit 1
    fi
done

mkdir -p -- "$config_dir"
for component in "${components[@]}"; do
    source_dir="$repo_dir/$component"
    target="$config_dir/$component"
    if [[ -L "$target" && "$(readlink -f -- "$target")" == "$source_dir" ]]; then
        printf 'Already linked: %s -> %s\n' "$target" "$source_dir"
        continue
    fi
    ln -s -- "$source_dir" "$target"
    printf 'Linked: %s -> %s\n' "$target" "$source_dir"
done
