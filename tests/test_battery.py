import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import contextlib
import io
import json
import subprocess

spec = importlib.util.spec_from_file_location(
    "battery", Path(__file__).resolve().parents[1] / "waybar/scripts/battery.py"
)
battery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(battery)


def device(kind="keyboard", model="Air75 V3-2", level="100%", state="unknown", present="yes", path="keyboard_dev_NEW"):
    return f"""Device: /org/freedesktop/UPower/devices/{path}
  model:                {model}
  {kind}
    present:             {present}
    state:               {state}
    percentage:          {level}
"""


class BatteryTests(unittest.TestCase):
    def test_changed_bluetooth_identifier(self):
        status = battery.battery_status(device(), "keyboard", "Air75")
        self.assertEqual(status["percentage"], 100)

    def test_missing_wired_telemetry(self):
        status = battery.battery_status(device(), "mouse", "Keychron M6")
        self.assertIn("N/A", status["text"])
        self.assertNotIn("percentage", status)

    def test_unknown_and_absent_are_not_zero(self):
        for report in ("", device(level="0% (should be ignored)"), device(present="no")):
            with self.subTest(report=report):
                self.assertEqual(battery.battery_status(report, "keyboard")["class"], "unavailable")

    def test_reported_zero_is_valid(self):
        status = battery.battery_status(device(level="0%"), "keyboard")
        self.assertEqual(status["percentage"], 0)
        self.assertNotIn("N/A", status["text"])

    def test_usb_charging(self):
        report = device("mouse", "Keychron M6", "62%", "charging", path="hiddev_usb_mouse")
        status = battery.battery_status(report, "mouse", "Keychron M6")
        self.assertEqual(status["percentage"], 62)
        self.assertEqual(status["class"], "charging")
        self.assertIn("charging", status["tooltip"])

    def test_model_filter(self):
        report = device(model="Other keyboard", level="1%") + device(level="87%")
        self.assertEqual(battery.battery_status(report, "keyboard", "Air75")["percentage"], 87)

    def test_service_failure(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("upower", 5)):
            with patch("sys.argv", ["battery.py", "mouse"]), patch.object(
                battery.subprocess, "check_output", side_effect=error
            ), contextlib.redirect_stdout(io.StringIO()) as output:
                battery.main()
                self.assertEqual(json.loads(output.getvalue())["class"], "unavailable")


if __name__ == "__main__":
    unittest.main()
