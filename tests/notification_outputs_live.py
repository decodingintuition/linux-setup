import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import sys

binary = sys.argv[-1]
root = Path(__file__).resolve().parents[1]

def client(*args):
    return subprocess.check_output(['swaync-client', *args], text=True, timeout=5).strip()

def popups(pid):
    layers = json.loads(subprocess.check_output(['hyprctl', 'layers', '-j'], text=True))
    return sorted(output for output, data in layers.items() if any(
        layer['pid'] == pid and layer['namespace'] == 'swaync-notification-window'
        for level in data['levels'].values() for layer in level
    ))

def check():
    with tempfile.TemporaryDirectory() as directory:
        config = json.loads((root / 'swaync/config.json').read_text())
        path = Path(directory) / 'config.json'
        config['notification-window-outputs'] = 'none'
        path.write_text(json.dumps(config))
        with (Path(directory) / 'daemon.log').open('w+') as log:
            env = dict(os.environ, GSETTINGS_BACKEND='memory', GTK_A11Y='none', GIO_USE_VFS='local')
            process = subprocess.Popen([binary, '-c', str(path), '-s', str(root / 'swaync/style.css')], env=env, stdout=log, stderr=log)
            try:
                for _ in range(50):
                    if process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        owned = subprocess.check_output([
                            'gdbus', 'call', '--session', '--dest', 'org.freedesktop.DBus',
                            '--object-path', '/org/freedesktop/DBus', '--method',
                            'org.freedesktop.DBus.NameHasOwner', 'org.erikreider.swaync.cc',
                        ], text=True)
                        if 'true' in owned:
                            break
                        time.sleep(.1)
                    except subprocess.CalledProcessError:
                        time.sleep(.1)
                assert client('-D') == 'false'
                for selected in (['DP-1'], ['DP-2'], ['DP-1','DP-2'], []):
                    client('--hide-all')
                    config['notification-window-outputs'] = ','.join(selected) or 'none'
                    path.write_text(json.dumps(config))
                    client('-R')
                    subprocess.run(['notify-send', '-p', '-t', '60000', 'Display routing check'], check=True, stdout=subprocess.DEVNULL)
                    time.sleep(.6)
                    actual=popups(process.pid)
                    assert actual == selected, (selected, actual)
                    assert client('-D') == 'false'
                    print('Verified outputs:', selected)
                assert client('-c') == '4', client('-c')
                config['notification-window-outputs'] = 'DP-1,DP-2'
                path.write_text(json.dumps(config))
                client('-R')
                client('-dn')
                subprocess.run(['notify-send', 'Do Not Disturb routing check'], check=True)
                time.sleep(.4)
                assert popups(process.pid) == []
                assert client('-D') == 'true'
                client('-df')
                subprocess.run(['notify-send', '-t', '60000', 'Mirrored dismissal check'], check=True)
                time.sleep(.4)
                assert popups(process.pid) == ['DP-1','DP-2']
                client('--close-latest')
                time.sleep(.6)
                assert popups(process.pid) == []
                print('Verified shared history, Do Not Disturb, and mirrored dismissal')
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        raise SystemExit(subprocess.call(['dbus-run-session', '--', sys.executable, __file__, '--isolated', binary]))
    if len(sys.argv) != 3 or sys.argv[1] != '--isolated':
        raise SystemExit('Usage: python3 tests/notification_outputs_live.py /path/to/patched/swaync')
    check()
