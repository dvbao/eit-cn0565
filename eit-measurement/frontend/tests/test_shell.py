"""Step 4: the window shell (header, exactly three tabs, read-only configuration column, honest empty states)."""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no screen needed
ROOT = Path(__file__).resolve().parents[2]  # eit-measurement/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from frontend.app import create_app  # noqa: E402
from frontend.main_window import TABS, MainWindow  # noqa: E402

APP = create_app([])


def texts(widget):
    from PySide6.QtWidgets import QLabel

    return " | ".join(lab.text() for lab in widget.findChildren(QLabel))


class ShellTests(unittest.TestCase):
    def test_exactly_three_tabs(self):
        w = MainWindow()
        self.assertEqual([w.tabs.tabText(i) for i in range(w.tabs.count())], list(TABS))
        self.assertEqual(list(TABS), ["Measurement", "Results", "Sessions"])

    def test_header_shows_confirmed_state_and_clock(self):
        w = MainWindow()
        self.assertIn("Disconnected", w.header.device.text())
        self.assertRegex(w.header.clock.text(), r"^\d\d:\d\d:\d\d$")

    def test_configuration_column_shows_backend_values(self):
        w = MainWindow()
        shown = texts(w.measurement.config)
        for expected in ("<b>16</b>", "<b>208</b>", "<b>20.6 s</b>", "<b>39</b>", "<b>23.1 s</b>", "<b>17.0 min</b>"):
            self.assertIn(expected, shown)

    def test_no_fake_countdown_and_start_locked(self):
        w = MainWindow()  # keep the window alive: Qt deletes children with their parent
        self.assertEqual(w.measurement.guidance.countdown.text(), "--:--")
        self.assertFalse(w.measurement.guidance.start_button.isEnabled())
        self.assertFalse(w.measurement.config.connect_button.isEnabled())

    def test_empty_data_folder_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["EIT_DATA_ROOT"] = tmp
            try:
                w = MainWindow()
                shown = texts(w.measurement.config)
            finally:
                del os.environ["EIT_DATA_ROOT"]
        self.assertIn("No measurement settings found", shown)
        self.assertIsNone(re.search(r"<b>208</b>", shown))


if __name__ == "__main__":
    unittest.main()
