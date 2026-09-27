#!/usr/bin/env python3
"""Show reported peripheral battery levels without treating missing data as zero."""

import argparse
import json
import os
import re
import subprocess

ICONS = {"mouse": "󰍽", "keyboard": "󰌌"}


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
        return {
            "text": f"{ICONS[kind]} N/A",
            "tooltip": f"{model or kind.title()}: no battery level reported",
            "class": "unavailable",
        }

    fields, value = max(candidates, key=lambda item: item[0].get("state") == "charging")
    state = fields.get("state", "unknown")
    charging = state == "charging"
    level = f"{value:g}%"
    tooltip = f"{fields.get('model', kind.title())}: {level}"
    if state != "unknown":
        tooltip += f" · {state.replace('-', ' ')}"
    return {
        "text": f"{ICONS[kind]} {level}" + (" ⚡" if charging else ""),
        "tooltip": tooltip,
        "class": "charging" if charging else "battery",
        "percentage": value,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=ICONS)
    parser.add_argument("--model", default="")
    args = parser.parse_args()
    try:
        report = subprocess.check_output(
            ["upower", "--dump"], text=True, timeout=5,
            stderr=subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        report = ""
    print(json.dumps(battery_status(report, args.kind, args.model)))


if __name__ == "__main__":
    main()
