import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("notification_layout", ROOT / "swaync/scripts/start.py")
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


class NotificationLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gresource") and Path(layout.BINARY).exists(), "SwayNC is required")
    def test_installed_template_keeps_controls_and_frees_body_width(self):
        original = ET.fromstring(subprocess.check_output(
            ["gresource", "extract", layout.BINARY, layout.RESOURCE], text=True
        ))
        updated = ET.fromstring(layout.header_icon_layout(ET.tostring(original)))
        ids = lambda root: sorted(node.get("id") for node in root.iter() if node.get("id"))
        self.assertEqual(ids(original), ids(updated))
        parents = {child: parent for parent in updated.iter() for child in parent}
        summary = updated.find(".//object[@id='summary']")
        body = updated.find(".//object[@id='body']")
        header = parents[parents[summary]]
        self.assertIsNotNone(header.find("child/object/property/object[@id='img']"))
        text_box = parents[parents[body]]
        self.assertIs(parents[parents[header]], text_box)
        row = parents[parents[text_box]]
        self.assertEqual(len(row.findall("child")), 1)
        for original_node in original.findall(".//object[@id]"):
            if original_node.get("id") in {
                "revealer", "dismissible_widget", "base_widget", "base_box", "default_action"
            }:
                continue
            updated_node = updated.find(f".//object[@id='{original_node.get('id')}']")
            self.assertEqual(ET.tostring(original_node), ET.tostring(updated_node))

    def test_incompatible_template_is_rejected(self):
        with self.assertRaises(ValueError):
            layout.header_icon_layout("<interface><object id='summary'/></interface>")

    def test_incompatible_template_still_starts_notifications(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = {"XDG_RUNTIME_DIR": directory, "G_RESOURCE_OVERLAYS": "/other=/tmp/other"}
            with patch.dict(os.environ, environment, clear=True), \
                    patch.object(layout.subprocess, "check_output", return_value="<interface/>"), \
                    patch.object(layout.os, "execve") as execute, \
                    patch.object(layout.sys, "argv", ["start.py"]), \
                    patch.object(layout.sys, "stderr"):
                layout.main()
            execute.assert_called_once_with(layout.BINARY, [layout.BINARY], environment)
            self.assertFalse((Path(directory) / "swaync-layout").exists())


if __name__ == "__main__":
    unittest.main()
