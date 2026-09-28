#!/usr/bin/env python3
"""Start SwayNC with the notification icon in the title row."""

import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

RESOURCE = "/org/erikreider/swaync/ui/notification.ui"
BINARY = "/usr/bin/swaync"


def header_icon_layout(template):
    root = ET.fromstring(template)
    parents = {child: parent for parent in root.iter() for child in parent}
    image = root.find(".//object[@id='img']")
    summary = root.find(".//object[@id='summary']")
    body = root.find(".//object[@id='body']")
    try:
        overlay = parents[parents[image]]
        icon_child = parents[overlay]
        row = parents[icon_child]
        header = parents[parents[summary]]
        text_box = parents[parents[body]]
        if (
            overlay.get("class") != "GtkOverlay"
            or icon_child.tag != "child"
            or header.get("class") != "GtkBox"
            or parents[parents[header]] is not text_box
            or parents[parents[text_box]] is not row
        ):
            raise ValueError("Unrecognized notification layout")
    except KeyError as error:
        raise ValueError("Unrecognized notification layout") from error
    row.remove(icon_child)
    header.insert(list(header).index(header.find("child")), icon_child)
    return ET.tostring(root, encoding="unicode")


def main():
    environment = os.environ.copy()
    try:
        template = subprocess.check_output(
            ["gresource", "extract", BINARY, RESOURCE], text=True, timeout=5
        )
        layout = header_icon_layout(template)
        directory = Path(environment["XDG_RUNTIME_DIR"]) / "swaync-layout"
        directory.mkdir(mode=0o700, exist_ok=True)
        target = directory / "notification.ui"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(layout)
        temporary.replace(target)
        overlays = environment.get("G_RESOURCE_OVERLAYS", "")
        environment["G_RESOURCE_OVERLAYS"] = f"{RESOURCE}={target}" + (
            f":{overlays}" if overlays else ""
        )
    except (OSError, KeyError, ValueError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"SwayNC layout override unavailable, using packaged layout: {error}", file=sys.stderr)
    os.execve(BINARY, [BINARY, *sys.argv[1:]], environment)


if __name__ == "__main__":
    main()
