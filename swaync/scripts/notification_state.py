"""Persist notification display choices separately from shared configuration."""

import json
from pathlib import Path
import tempfile

OUTPUTS = ("DP-1", "DP-2")
DEFAULT_OUTPUTS = ["DP-2"]


def write_json(target, value):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=target.parent,
                                         prefix=".notification-", delete=False) as file:
            temporary = Path(file.name)
            file.write(json.dumps(value, indent=4) + "\n")
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_outputs(config_dir, outputs):
    if any(output not in OUTPUTS for output in outputs):
        raise ValueError("Unknown notification output")
    selected = [output for output in OUTPUTS if output in outputs]
    write_json(Path(config_dir) / "monitors.local.json", {"outputs": selected})
    return selected


def load_outputs(config_dir):
    target = Path(config_dir) / "monitors.local.json"
    if not target.exists():
        config = Path(config_dir) / "config.json"
        output = json.loads(config.read_text()).get("notification-window-preferred-output") if config.exists() else None
        return save_outputs(config_dir, [output] if output in OUTPUTS else DEFAULT_OUTPUTS)
    outputs = json.loads(target.read_text())["outputs"]
    if not isinstance(outputs, list) or any(output not in OUTPUTS for output in outputs):
        raise ValueError("Invalid notification output selection")
    return [output for output in OUTPUTS if output in outputs]


def runtime_config(config_dir, runtime_dir):
    config_dir = Path(config_dir)
    config = json.loads((config_dir / "config.json").read_text())
    outputs = load_outputs(config_dir)
    config["notification-window-outputs"] = ",".join(outputs) or "none"
    actions = config["widget-config"]["buttons-grid#notification-monitor"]["actions"]
    for action in actions:
        action["active"] = action["label"] in outputs
    target = Path(runtime_dir) / "swaync-displays/config.json"
    write_json(target, config)
    return target
