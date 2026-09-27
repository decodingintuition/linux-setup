import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "notification_monitor", ROOT / "swaync/scripts/notification-monitor.py"
)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class NotificationMonitorTests(unittest.TestCase):
    def test_selection_persists_without_changing_other_settings(self):
        original = json.loads((ROOT / "swaync/config.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps(original))
            for output, index in (("DP-1", 0), ("DP-2", 1), ("DP-2", 1)):
                monitor.select_monitor(config, output)
                saved = json.loads(config.read_text())
                self.assertEqual(saved["notification-window-preferred-output"], output)
                actions = saved["widget-config"]["buttons-grid#notification-monitor"]["actions"]
                self.assertEqual([a["active"] for a in actions], [index == 0, index == 1])
                expected = json.loads(json.dumps(original))
                expected["notification-window-preferred-output"] = output
                for i, action in enumerate(expected["widget-config"]["buttons-grid#notification-monitor"]["actions"]):
                    action["active"] = i == index
                self.assertEqual(saved, expected)

    def test_symlink_and_file_permissions_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tracked.json"
            target.write_text((ROOT / "swaync/config.json").read_text())
            target.chmod(0o640)
            link = Path(directory) / "config.json"
            link.symlink_to(target)
            monitor.select_monitor(link, "DP-1")
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
            self.assertEqual(json.loads(target.read_text())["notification-window-preferred-output"], "DP-1")
            self.assertFalse(list(Path(directory).glob(".monitor-*")))


if __name__ == "__main__":
    unittest.main()
