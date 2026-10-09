#!/usr/bin/env python3
"""Share native Wayland gamma between Waybar and the ARC Raiders shortcut."""
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import socket
import time
import hashlib


def read_state(path):
    try:
        current, selected = map(float, path.read_text().split())
        if math.isfinite(current) and math.isfinite(selected) and 1 <= current <= 3 and 1 < selected <= 3:
            return current, selected
    except (OSError, ValueError):
        pass
    return 1.0, 3.0


def migrate(runtime):
    marker = runtime / "hypr-gamma-native"
    if marker.exists():
        return False
    actual = json.loads(subprocess.check_output(
        ["hyprctl", "-j", "getoption", "decoration:screen_shader"], text=True))["str"]
    old_shader = actual.startswith(str(runtime / "hypr-gamma") + "/")
    settings = {}
    saved = runtime / "hypr-gamma-damage-tracking"
    if saved.exists():
        settings["damage_tracking"] = int(saved.read_text())
    saved = runtime / "hypr-gamma-vfr"
    if saved.exists():
        settings["vfr"] = saved.read_text().strip() == "true"
    parts = []
    if old_shader:
        parts.append('decoration={screen_shader=""}')
    if settings:
        parts.append("debug={" + ",".join(f"{key}={str(value).lower()}" for key, value in settings.items()) + "}")
    if parts:
        result = subprocess.run(["hyprctl", "eval", "hl.config({" + ",".join(parts) + "})"],
                                capture_output=True, text=True, check=True)
        if result.stdout.strip() != "ok":
            raise RuntimeError(result.stdout.strip() or result.stderr.strip())
    marker.write_text("wayland-v1\n")
    return old_shader


def socket_path(runtime):
    instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "default")
    suffix = hashlib.sha256(instance.encode()).hexdigest()[:12]
    return runtime / f"hypr-gamma-{suffix}.sock"


def connect(path):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(2)
    try:
        connection.connect(str(path))
    except OSError:
        connection.close()
        raise
    return connection


def apply(runtime, value):
    path = socket_path(runtime)
    failed = path.with_suffix(".failed")
    if value > 1 and failed.exists() and time.time() - failed.stat().st_mtime < 30:
        raise RuntimeError("Native gamma is unavailable in this desktop session")
    try:
        connection = connect(path)
    except (FileNotFoundError, ConnectionRefusedError):
        path.unlink(missing_ok=True)
        if value == 1:
            return
        controller = Path(__file__).resolve().parent.parent / "modules/gamma-control"
        if not controller.exists():
            raise RuntimeError("Build the gamma service with waybar/scripts/build-gamma.sh")
        with (runtime / "hypr-gamma-native.log").open("a") as log:
            process = subprocess.Popen([str(controller), str(path)], stdout=log, stderr=log,
                                       start_new_session=True, umask=0o077)
        deadline = time.monotonic() + 2
        while True:
            try:
                connection = connect(path)
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if process.poll() is not None or time.monotonic() >= deadline:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=2)
                    failed.write_text("unavailable\n")
                    raise RuntimeError("Native gamma is unavailable in this desktop session")
                time.sleep(0.02)
    with connection:
        connection.sendall(f"{value:.2f}\n".encode())
        if connection.recv(64) != b"ok\n":
            raise RuntimeError("The compositor rejected the native gamma update")
    failed.unlink(missing_ok=True)


def write_state(state, current, selected):
    temporary = state.with_name(state.name + f".{os.getpid()}.tmp")
    try:
        temporary.write_text(f"{current:.2f} {selected:.2f}\n")
        temporary.replace(state)
    finally:
        temporary.unlink(missing_ok=True)


def main(args):
    value = None
    if args not in (["toggle"], ["status"]):
        if len(args) != 2 or args[0] != "set":
            raise ValueError("Usage: gamma.py status | toggle | set VALUE")
        value = float(args[1])
        if not math.isfinite(value) or not 1 <= value <= 3:
            raise ValueError("Gamma must be between 1 and 3")
        value = round(value, 2)
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    state = runtime / "hypr-gamma-state"
    with (runtime / "hypr-gamma-toggle.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current, selected = read_state(state)
        if migrate(runtime):
            current = 1.0
            write_state(state, current, selected)
        if args == ["status"]:
            apply(runtime, current)
        else:
            previous = current
            current = (1.0 if current > 1 else selected) if args == ["toggle"] else value
            if current > 1:
                selected = current
            if current != previous:
                apply(runtime, current)
        write_state(state, current, selected)
    print(f"{current:.2f} {selected:.2f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    reply = None
    if len(args) >= 2 and args[-2] == "--reply-file":
        reply = Path(args[-1])
        args = args[:-2]
    outcome = "error\n"
    try:
        main(args)
        outcome = "ok\n"
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
    finally:
        if reply:
            reply.write_text(outcome)
