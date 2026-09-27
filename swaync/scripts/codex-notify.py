#!/usr/bin/env python3
"""Deliver Codex turn-completion events to the desktop notification service."""

import html
import json
import os
from pathlib import Path
import subprocess
import sys


def clean_text(value, limit):
    if not isinstance(value, str):
        return ""
    text = " ".join("".join(c for c in value if c.isprintable() or c.isspace()).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def notify(event):
    if not isinstance(event, dict) or event.get("type") != "agent-turn-complete":
        return
    cwd = event.get("cwd")
    project = clean_text(Path(cwd).name, 60) if isinstance(cwd, str) and cwd else "Codex"
    thread_id = event.get("thread-id")
    session = clean_text(thread_id[-8:], 8) if isinstance(thread_id, str) else ""
    title = f"Codex finished: {project}"
    if session:
        title += f" [{session}]"
    body = clean_text(event.get("last-assistant-message"), 240) or "Turn complete."
    environment = os.environ.copy()
    if not environment.get("DBUS_SESSION_BUS_ADDRESS"):
        runtime = environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        bus = Path(runtime) / "bus"
        if bus.is_socket():
            environment["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
    try:
        subprocess.run(
            ["notify-send", "--app-name=Codex", "--icon=utilities-terminal",
             "--urgency=normal", "--expire-time=8000", "--", title, html.escape(body)],
            env=environment, check=False, timeout=3,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def main():
    if len(sys.argv) != 2:
        return
    try:
        event = json.loads(sys.argv[1])
    except (ValueError, TypeError):
        return
    notify(event)


if __name__ == "__main__":
    main()
