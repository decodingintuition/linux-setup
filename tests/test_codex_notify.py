import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

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
