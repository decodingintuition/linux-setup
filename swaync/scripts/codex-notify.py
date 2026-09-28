#!/usr/bin/env python3
"""Deliver Codex turn-completion events to the desktop notification service."""

import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys


INLINE_MARKDOWN = re.compile(
    r"(?P<ticks>`+)(?P<code>.+?)(?P=ticks)"
    r"|\*\*(?P<bold>\S(?:.*?\S)?)\*\*"
    r"|(?<!\w)__(?P<bold_under>\S(?:.*?\S)?)__(?!\w)"
    r"|(?<!\*)\*(?P<italic>\S(?:[^*]*?\S)?)\*(?!\*)"
    r"|(?<!\w)_(?P<italic_under>\S(?:[^_]*?\S)?)_(?!\w)"
    r"|\[(?P<link>[^\]]+)\]\((?:<[^>]+>|[^)]+)\)"
)


def clean_text(value, limit):
    if not isinstance(value, str):
        return ""
    text = " ".join("".join(c for c in value if c.isprintable() or c.isspace()).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def notification_body(value, limit=240):
    text = clean_text(value, sys.maxsize)
    if not text:
        return "Turn complete."
    parts = []
    start = 0
    for match in INLINE_MARKDOWN.finditer(text):
        parts.append((text[start:match.start()], None))
        for group, tag in (("code", "tt"), ("bold", "b"), ("bold_under", "b"),
                           ("italic", "i"), ("italic_under", "i"), ("link", None)):
            if match.group(group) is not None:
                parts.append((match.group(group), tag))
                break
        start = match.end()
    parts.append((text[start:], None))
    truncated = sum(len(content) for content, _ in parts) > limit
    remaining = limit - 1 if truncated else limit
    result = []
    for content, tag in parts:
        if remaining <= 0:
            break
        content = content[:remaining]
        remaining -= len(content)
        escaped = html.escape(content)
        result.append(f"<{tag}>{escaped}</{tag}>" if tag and content else escaped)
    if truncated:
        result.append("…")
    return "".join(result)


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
    body = notification_body(event.get("last-assistant-message"))
    environment = os.environ.copy()
    if not environment.get("DBUS_SESSION_BUS_ADDRESS"):
        runtime = environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        bus = Path(runtime) / "bus"
        if bus.is_socket():
            environment["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
    try:
        subprocess.run(
            ["notify-send", "--app-name=Codex", "--icon=utilities-terminal",
             "--urgency=normal", "--expire-time=8000", "--", title, body],
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
