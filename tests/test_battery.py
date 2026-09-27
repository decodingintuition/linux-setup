import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import contextlib
import io
import json
import subprocess
import os
import select
import sys
import tempfile
import time
from unittest.mock import Mock

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

    def test_keychron_charging_bit_and_zero(self):
        for packed, expected in ((198, (70, "charging")), (0, (0, "discharging")),
                                 (228, (100, "charging"))):
            packet = b"\xb4\x06" + bytes(18) + bytes([packed]) + bytes(43)
            self.assertEqual(battery.parse_keychron(packet), expected)

    def test_keychron_invalid_reports(self):
        for packet in (b"", b"\xb4\x06", b"\xb4\x07" + bytes(62),
                       b"\xb4\x06" + bytes(18) + b"\xff" + bytes(43)):
            self.assertIsNone(battery.parse_keychron(packet))

    def test_airpods_max_live_packet(self):
        self.assertEqual(battery.parse_airpods(bytes.fromhex("040004000400010101640201")),
                         (100, "discharging"))
        self.assertEqual(battery.parse_airpods(bytes.fromhex("040004000400010101000101")),
                         (0, "charging"))

    def test_airpods_invalid_or_disconnected(self):
        for packet in ("040004000400010101640301", "040004000400010101ff0201",
                       "040004000400020101640201", "040004000400010801640201",
                       "04000400040001", "0400040006000000"):
            self.assertIsNone(battery.parse_airpods(bytes.fromhex(packet)))

    def test_headphones_disconnect_clears_reading(self):
        reader = battery.Reader("headphones", "AirPods Max")
        reader.airpods.address = "90:62:3F:9B:11:C3"
        reader.airpods.reading = (100, "discharging")
        reader.airpods.sock = Mock()
        reader.bluetooth.devices = Mock(return_value={})
        with patch.object(battery, "upower_status", return_value=battery.status("headphones", "AirPods Max")):
            self.assertNotIn("percentage", reader.poll())
        self.assertIsNone(reader.airpods.reading)
        self.assertIsNone(reader.airpods.sock)

    def test_airpods_reconnect_after_transport_error(self):
        reader = battery.AirPods()
        transport = Mock()
        transport.recv.return_value = bytes.fromhex("010004000000010003000c00010000000000")
        with patch.object(battery.socket, "socket", return_value=transport), patch.object(
            battery.select, "select", return_value=([], [], [])
        ), patch.object(battery.time, "monotonic", return_value=100):
            reader.poll("90:62:3F:9B:11:C3")
        self.assertEqual(transport.send.call_count, 2)
        reader.reading = (100, "discharging")
        transport.recv.side_effect = ConnectionResetError()
        with patch.object(battery.select, "select", return_value=([transport], [], [])):
            self.assertIsNone(reader.poll(reader.address))
        self.assertIsNone(reader.sock)
        replacement = Mock()
        replacement.recv.return_value = bytes.fromhex("01000400")
        with patch.object(battery.socket, "socket", return_value=replacement), patch.object(
            battery.select, "select", return_value=([], [], [])
        ), patch.object(battery.time, "monotonic", return_value=116):
            reader.poll(reader.address)
        replacement.connect.assert_called_once()

    def test_keyboard_bluetooth_zero_without_invented_charging(self):
        reader = battery.Reader("keyboard", "Air75")
        reader.bluetooth.devices = Mock(return_value={"device": {
            "org.bluez.Device1": {"Name": "Air75 V3-2", "Connected": True, "Icon": "input-keyboard"},
            "org.bluez.Battery1": {"Percentage": 0},
        }})
        result = reader.poll()
        self.assertEqual(result["percentage"], 0)
        self.assertEqual(result["class"], "battery")
        self.assertNotIn("charging", result["tooltip"])

    def test_disconnected_bluetooth_upower_cache_is_ignored(self):
        report = device() + "    native-path: /org/bluez/hci0/dev_OLD\n"
        with patch.object(battery.subprocess, "check_output", return_value=report):
            self.assertNotIn("percentage", battery.upower_status("keyboard", "Air75", wired_only=True))

    def test_two_bars_share_polling_and_survive_leader_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "polls"
            code = """
import importlib.util, os, sys, time
spec = importlib.util.spec_from_file_location('battery', sys.argv[1])
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
def poll(self):
    with open(sys.argv[2], 'a') as f:
        f.write(str(os.getpid()) + ' ' + str(time.monotonic()) + '\\n')
    return b.status('mouse', 'test', 70, 'charging')
b.Reader.poll = poll
b.stream('mouse', 'test')
"""
            processes = []
            try:
                for _ in range(2):
                    processes.append(subprocess.Popen(
                        [sys.executable, "-u", "-c", code, str(Path(battery.__file__)), str(log)],
                        env={**os.environ, "XDG_RUNTIME_DIR": directory},
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    ))
                for process in processes:
                    self.assertTrue(select.select([process.stdout], [], [], 4)[0])
                    json.loads(process.stdout.readline())
                deadline = time.monotonic() + 4
                while len(log.read_text().splitlines()) < 3 and time.monotonic() < deadline:
                    time.sleep(0.05)
                polls = [line.split() for line in log.read_text().splitlines()]
                self.assertGreaterEqual(len(polls), 3)
                self.assertEqual(len({pid for pid, _ in polls}), 1)
                self.assertTrue(all(float(b[1]) - float(a[1]) >= 0.9 for a, b in zip(polls, polls[1:])))
                leader = next(p for p in processes if p.pid == int(polls[0][0]))
                leader.terminate()
                leader.wait(timeout=2)
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    if len({line.split()[0] for line in log.read_text().splitlines()}) == 2:
                        break
                    time.sleep(0.05)
                self.assertEqual(len({line.split()[0] for line in log.read_text().splitlines()}), 2)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    process.communicate(timeout=3)


if __name__ == "__main__":
    unittest.main()
