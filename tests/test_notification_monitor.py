import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'swaync/scripts'))
spec = importlib.util.spec_from_file_location(
    'notification_monitor', ROOT / 'swaync/scripts/notification-monitor.py'
)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class NotificationMonitorTests(unittest.TestCase):
    def test_independent_selections_preserve_configuration_and_dnd(self):
        original = (ROOT / 'swaync/config.json').read_text()
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(original)
            monitor.save_outputs(config.parent, ['DP-1'])
            for output, enabled, expected in (
                ('DP-2', True, ['DP-1', 'DP-2']),
                ('DP-1', False, ['DP-2']),
                ('DP-2', False, []),
                ('DP-1', True, ['DP-1']),
                ('DP-1', True, ['DP-1']),
            ):
                runtime = monitor.select_monitor(config, output, enabled, directory)
                self.assertEqual(monitor.load_outputs(config.parent), expected)
                saved = json.loads(runtime.read_text())
                self.assertEqual(saved['notification-window-outputs'], ','.join(expected) or 'none')
                actions = saved['widget-config']['buttons-grid#notification-monitor']['actions']
                self.assertEqual([a['active'] for a in actions], [o in expected for o in monitor.OUTPUTS])
                self.assertIn('dnd', saved['widgets'])
                self.assertEqual(saved['widget-config']['dnd'], json.loads(original)['widget-config']['dnd'])
                self.assertEqual(config.read_text(), original)

    def test_migration_preserves_selected_output_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'tracked.json'
            config = json.loads((ROOT / 'swaync/config.json').read_text())
            config['notification-window-preferred-output'] = 'DP-1'
            target.write_text(json.dumps(config))
            target.chmod(0o640)
            link = Path(directory) / 'config.json'
            link.symlink_to(target)
            self.assertEqual(monitor.load_outputs(link.parent), ['DP-1'])
            monitor.select_monitor(link, 'DP-2', True, directory)
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
            self.assertEqual(json.loads(target.read_text()), config)

    def test_invalid_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                monitor.save_outputs(directory, ['unknown'])


if __name__ == '__main__':
    unittest.main()
