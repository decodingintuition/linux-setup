#!/usr/bin/env python3
"""Show reported peripheral battery levels without treating missing data as zero."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import time

ICONS = {"mouse": "󰍽", "keyboard": "󰌌", "headphones": "󰋋"}


def status(kind, model, value=None, state="unknown", source=""):
    if value is None:
        return {"text": f"{ICONS[kind]} N/A", "class": "unavailable",
                "tooltip": f"{model or kind.title()}: no battery level reported"}
    charging = state == "charging"
    tooltip = f"{model or kind.title()}: {value:g}%"
    if state != "unknown":
        tooltip += f" · {state.replace('-', ' ')}"
    if source:
        tooltip += f"\n{source}"
    return {"text": f"{ICONS[kind]} {value:g}%" + (" ⚡" if charging else ""),
            "tooltip": tooltip, "class": "charging" if charging else "battery",
            "percentage": value}


def battery_status(report, kind, model=""):
    candidates = []
    for block in re.split(r"^Device: ", report, flags=re.MULTILINE)[1:]:
        if not re.search(rf"^  {kind}\s*$", block, re.MULTILINE):
            continue
        fields = dict(re.findall(r"^\s+([a-z-]+):\s*(.*?)$", block, re.MULTILINE))
        if model.casefold() not in fields.get("model", "").casefold():
            continue
        if fields.get("present") != "yes":
            continue
        percentage = re.fullmatch(r"(\d+(?:\.\d+)?)%", fields.get("percentage", ""))
        if not percentage:
            continue
        value = float(percentage[1])
        if 0 <= value <= 100:
            candidates.append((fields, value))

    if not candidates:
        return status(kind, model)

    fields, value = max(candidates, key=lambda item: item[0].get("state") == "charging")
    return status(kind, fields.get("model", kind.title()), value,
                  fields.get("state", "unknown"), "UPower")


def upower_status(kind, model, wired_only=False):
    try:
        report = subprocess.check_output(
            ["upower", "--dump"], text=True, timeout=5,
            stderr=subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        report = ""
    if wired_only:
        report = "".join("Device: " + block for block in re.split(
            r"^Device: ", report, flags=re.MULTILINE)[1:]
            if not re.search(r"native-path:\s*/org/bluez/", block))
    return battery_status(report, kind, model)


def parse_keychron(data):
    if len(data) >= 21 and data[:2] == b"\xb4\x06" and data[20] & 127 <= 100:
        return data[20] & 127, "charging" if data[20] & 128 else "discharging"
    return None


def keychron_battery():
    for entry in Path("/sys/class/hidraw").glob("*"):
        try:
            if "HID_ID=0003:00003434:0000D060" not in (entry / "device/uevent").read_text():
                continue
            descriptor = (entry / "device/report_descriptor").read_bytes()
            if b"\x06\xc1\xff" not in descriptor or b"\x85\xb3" not in descriptor:
                continue
            fd = os.open("/dev/" + entry.name, os.O_RDWR | os.O_NONBLOCK)
            try:
                # Keychron Launcher GET base information, including packed battery state.
                os.write(fd, b"\xb3\x06" + bytes(62))
                deadline = time.monotonic() + 0.5
                while select.select([fd], [], [], max(0, deadline - time.monotonic()))[0]:
                    result = parse_keychron(os.read(fd, 64))
                    if result is not None:
                        return result
                    if time.monotonic() >= deadline:
                        break
            finally:
                os.close(fd)
        except OSError:
            continue
    return None


def parse_airpods(data):
    if len(data) < 7 or data[:6] != bytes.fromhex("040004000400"):
        return None
    count = data[6]
    if len(data) < 7 + count * 5:
        return None
    for offset in range(7, 7 + count * 5, 5):
        component, _, level, charging, _ = data[offset:offset + 5]
        if component == 1 and level <= 100 and charging in (1, 2):
            return level, "charging" if charging == 1 else "discharging"
    return None


class Bluetooth:
    def __init__(self):
        self.bus = None

    def devices(self):
        try:
            from gi.repository import Gio, GLib
        except ImportError:
            return {}
        try:
            if self.bus is None:
                self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            return self.bus.call_sync(
                "org.bluez", "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects",
                None, None, Gio.DBusCallFlags.NONE, 1000, None,
            ).unpack()[0]
        except GLib.Error:
            self.bus = None
            return {}


class AirPods:
    def __init__(self):
        self.sock = None
        self.address = None
        self.reading = None
        self.retry_at = 0
        self.connected_at = 0

    def close(self):
        if self.sock is not None:
            self.sock.close()
        self.sock = None
        self.reading = None

    def poll(self, address):
        if address != self.address:
            self.close()
            self.address = address
            self.retry_at = 0
        if not address:
            return None
        try:
            if self.sock is None:
                if time.monotonic() < self.retry_at:
                    return None
                self.retry_at = time.monotonic() + 15
                self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET,
                                          socket.BTPROTO_L2CAP)
                self.sock.settimeout(2)
                self.sock.connect((address, 0x1001))
                self.sock.send(bytes.fromhex("00000400010002000000000000000000"))
                if not self.sock.recv(4096).startswith(bytes.fromhex("01000400")):
                    raise OSError("Missing AirPods handshake")
                # Subscribe to status notifications without changing listening settings.
                self.sock.send(bytes.fromhex("040004000f00ffffffff"))
                self.sock.setblocking(False)
                self.connected_at = time.monotonic()
            for _ in range(64):
                if not select.select([self.sock], [], [], 0)[0]:
                    break
                data = self.sock.recv(4096)
                if not data or data == bytes.fromhex("00010000"):
                    raise OSError("AirPods disconnected")
                reading = parse_airpods(data)
                if reading is not None:
                    self.reading = reading
            if self.reading is None and time.monotonic() - self.connected_at > 5:
                self.close()
        except OSError:
            self.close()
        return self.reading


class Reader:
    def __init__(self, kind, model):
        self.kind, self.model = kind, model
        self.bluetooth = Bluetooth()
        self.airpods = AirPods()

    def poll(self):
        if self.kind == "mouse" and self.model.casefold() in "keychron m6":
            reading = keychron_battery()
            if reading is not None:
                return status(self.kind, "Keychron M6", *reading, "USB")
        devices = self.bluetooth.devices()
        for interfaces in devices.values():
            device = interfaces.get("org.bluez.Device1", {})
            name = device.get("Name", "")
            if not device.get("Connected") or self.model.casefold() not in name.casefold():
                continue
            icon = device.get("Icon", "")
            expected = {"mouse": "input-mouse", "keyboard": "input-keyboard",
                        "headphones": "audio-headphones"}[self.kind]
            if icon != expected:
                continue
            if self.kind == "headphones" and "airpods max" in name.casefold():
                reading = self.airpods.poll(device.get("Address"))
                if reading is not None:
                    return status(self.kind, name, *reading, "Bluetooth · AirPods notifications")
                return status(self.kind, name)
            value = interfaces.get("org.bluez.Battery1", {}).get("Percentage")
            if isinstance(value, int) and 0 <= value <= 100:
                return status(self.kind, name, value, source="Bluetooth · device-reported level")
        self.airpods.poll(None)
        return upower_status(self.kind, self.model, wired_only=True)


def stream(kind, model):
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "waybar-battery"
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = kind + "-" + hashlib.sha256(model.encode()).hexdigest()[:16]
    cache = runtime / (key + ".json")
    reader = Reader(kind, model)
    leader = False
    with (runtime / (key + ".lock")).open("w") as lock:
        while True:
            started = time.monotonic()
            if not leader:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    leader = True
                except BlockingIOError:
                    pass
            if leader:
                result = reader.poll()
                temporary = cache.with_suffix(".tmp")
                temporary.write_text(json.dumps(result))
                temporary.replace(cache)
            else:
                result = status(kind, model)
                try:
                    if time.time() - cache.stat().st_mtime < 5:
                        result = json.loads(cache.read_text())
                except (OSError, ValueError):
                    pass
            print(json.dumps(result), flush=True)
            time.sleep(max(0, 1 - (time.monotonic() - started)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=ICONS)
    parser.add_argument("--model", default="")
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.watch:
        stream(args.kind, args.model)
    else:
        print(json.dumps(upower_status(args.kind, args.model)))


if __name__ == "__main__":
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        os._exit(0)
