#!/usr/bin/env bash
set -euo pipefail

# Build a pinned SwayNC release with independent popup outputs, without replacing
# the system package. Requires vala, meson, ninja, sassc, blueprint-compiler and
# SwayNC's development dependencies.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_root="$(mktemp -d "${TMPDIR:-/tmp}/swaync-outputs.XXXXXX")"
trap 'rm -rf -- "$build_root"' EXIT
git clone --depth 1 --branch v0.12.6 https://github.com/ErikReider/SwayNotificationCenter.git "$build_root/source"
git -C "$build_root/source" apply "$script_dir/../patches/multiple-outputs.patch"
meson setup "$build_root/build" "$build_root/source" --buildtype=release -Dman-pages=false -Dsystemd-service=false
meson compile -C "$build_root/build"
meson test -C "$build_root/build"
destination="${XDG_DATA_HOME:-$HOME/.local/share}/linux-setup/swaync"
mkdir -p -- "$destination"
install -m 755 "$build_root/build/src/swaync" "$destination/swaync.new"
mv -- "$destination/swaync.new" "$destination/swaync"
