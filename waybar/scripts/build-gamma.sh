#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
modules="$root/modules"
build_dir="$(mktemp -d)"
trap 'rm -rf -- "$build_dir"' EXIT

cc -std=c11 -O2 -Wall -Wextra -Werror -shared -fPIC \
    "$modules/gamma-slider.c" $(pkg-config --cflags --libs gtk+-3.0) -lm \
    -o "$build_dir/gamma-slider.so"
install -m 755 "$build_dir/gamma-slider.so" "$modules/gamma-slider.so"
wayland-scanner client-header "$root/protocols/wlr-gamma-control-unstable-v1.xml" "$build_dir/gamma-protocol.h"
wayland-scanner private-code "$root/protocols/wlr-gamma-control-unstable-v1.xml" "$build_dir/gamma-protocol.c"
cc -std=c11 -O2 -Wall -Wextra -Werror -I"$build_dir" \
    "$modules/gamma-control.c" "$build_dir/gamma-protocol.c" \
    $(pkg-config --cflags --libs wayland-client) -lm -o "$build_dir/gamma-control"
install -m 755 "$build_dir/gamma-control" "$modules/gamma-control"
