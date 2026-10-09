#!/usr/bin/env python3
"""Toggle popup outputs independently without changing Do Not Disturb."""

import argparse
import fcntl
import os
from pathlib import Path
import subprocess

from notification_state import OUTPUTS, load_outputs, runtime_config, save_outputs


def select_monitor(config_path, output, enabled, runtime_dir):
    config_dir = Path(config_path).parent
    lock = Path(runtime_dir) / 'swaync-displays/selection.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('w') as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        outputs = load_outputs(config_dir)
        if enabled and output not in outputs:
            outputs.append(output)
        elif not enabled and output in outputs:
            outputs.remove(output)
        save_outputs(config_dir, outputs)
        return runtime_config(config_dir, runtime_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', nargs='?', choices=OUTPUTS)
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--reload', action='store_true')
    args = parser.parse_args()
    config_home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    config_dir = config_home / 'swaync'
    if args.status:
        if not args.output:
            parser.error('--status requires an output')
        print('true' if args.output in load_outputs(config_dir) else 'false')
        return
    runtime_dir = Path(os.environ['XDG_RUNTIME_DIR'])
    if args.reload:
        runtime_config(config_dir, runtime_dir)
    else:
        if not args.output:
            parser.error('an output or --reload is required')
        state = os.environ.get('SWAYNC_TOGGLE_STATE')
        if state not in ('true', 'false'):
            parser.error('SWAYNC_TOGGLE_STATE must be true or false')
        select_monitor(config_dir / 'config.json', args.output, state == 'true', runtime_dir)
    subprocess.run(['swaync-client', '-R', '-sw'], check=True, timeout=5)


if __name__ == '__main__':
    main()
