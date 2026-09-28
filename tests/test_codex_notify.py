import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location(
    "codex_notify", Path(__file__).resolve().parents[1] / "swaync/scripts/codex-notify.py"
)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class CodexNotifyTests(unittest.TestCase):
    def test_completion_sends_literal_escaped_preview(self):
        with patch.object(hook.subprocess, "run") as run:
            hook.notify({"type": "agent-turn-complete", "cwd": "/tmp/project",
                         "thread-id": "12345678-1234", "last-assistant-message": "Fixed <tag> & $(command)."})
        command = run.call_args.args[0]
        self.assertEqual(command[0], "notify-send")
        self.assertIn("project", command[-2])
        self.assertIn("[678-1234]", command[-2])
        self.assertEqual(command[-1], "Fixed &lt;tag&gt; &amp; $(command).")
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_other_events_and_malformed_payloads_are_ignored(self):
        with patch.object(hook.subprocess, "run") as run:
            for payload in (None, [], {}, {"type": "approval-requested"}):
                hook.notify(payload)
            for argument in ("not json", "null", "[]"):
                with patch("sys.argv", ["codex-notify.py", argument]):
                    hook.main()
            run.assert_not_called()

    def test_markdown_labels_are_rendered_before_sending(self):
        with patch.object(hook.subprocess, "run") as run:
            hook.notify({"type": "agent-turn-complete", "last-assistant-message":
                         "**Situation:** Fixed.\n\n**Result:** Ready."})
        self.assertEqual(run.call_args.args[0][-1], "<b>Situation:</b> Fixed. <b>Result:</b> Ready.")

    def test_basic_markdown_preserves_literal_code_and_link_labels(self):
        result = hook.notification_body(
            "__Bold__ and *italic* with _emphasis_, `a ** b < c`, "
            "[the file](/tmp/file.py), and snake_case_names."
        )
        self.assertEqual(result, "<b>Bold</b> and <i>italic</i> with <i>emphasis</i>, "
                         "<tt>a ** b &lt; c</tt>, the file, and snake_case_names.")

    def test_markup_is_escaped_inside_formatted_text(self):
        result = hook.notification_body('**<img src="/tmp/image"> & text**')
        self.assertEqual(result, '<b>&lt;img src=&quot;/tmp/image&quot;&gt; &amp; text</b>')

    def test_truncation_keeps_markup_balanced_and_counts_visible_text(self):
        result = hook.notification_body("**" + "<&" * 200 + "**")
        parsed = ET.fromstring("<body>" + result + "</body>")
        visible = "".join(parsed.itertext())
        self.assertEqual(len(visible), 240)
        self.assertTrue(visible.endswith("…"))
        self.assertEqual([node.tag for node in parsed], ["b"])

    def test_unmatched_markers_remain_literal(self):
        self.assertEqual(hook.notification_body("An unmatched **marker"), "An unmatched **marker")

    def test_missing_message_has_fallback(self):
        with patch.object(hook.subprocess, "run") as run:
            hook.notify({"type": "agent-turn-complete", "last-assistant-message": None})
        self.assertEqual(run.call_args.args[0][-1], "Turn complete.")

    def test_preview_is_bounded(self):
        preview = hook.clean_text("long\n" * 100, 240)
        self.assertEqual(len(preview), 240)
        self.assertNotIn("\n", preview)
        self.assertTrue(preview.endswith("…"))

    def test_notifier_failure_does_not_fail_the_hook(self):
        for failure in (FileNotFoundError(), subprocess.TimeoutExpired("notify-send", 3)):
            with patch.object(hook.subprocess, "run", side_effect=failure):
                hook.notify({"type": "agent-turn-complete"})


if __name__ == "__main__":
    unittest.main()
