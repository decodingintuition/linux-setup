#!/usr/bin/env python3
"""Save the popup monitor selected in the notification panel."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

MONITORS = {"DP-1": "Primary", "DP-2": "Second"}


def select_monitor(config_path, output):
    label = MONITORS[output]
    target = config_path.resolve(strict=True)
    config = json.loads(target.read_text())
    config["notification-window-preferred-output"] = output
    for action in config["widget-config"]["buttons-grid#notification-monitor"]["actions"]:
        action["active"] = action["label"] == label
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=target.parent,
                                         prefix=".monitor-", delete=False) as file:
            temporary = Path(file.name)
            file.write(json.dumps(config, indent=4, ensure_ascii=False) + "\n")
        temporary.chmod(target.stat().st_mode & 0o777)
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", choices=MONITORS)
    args = parser.parse_args()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    select_monitor(config_home / "swaync/config.json", args.output)
    subprocess.run(["swaync-client", "-R", "-sw"], check=True, timeout=5)


if __name__ == "__main__":
    main()
