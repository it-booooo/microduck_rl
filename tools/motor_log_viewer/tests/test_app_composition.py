"""End-to-end check that ApplicationComposer wires a loadable, working app.

Needs PySide6 (``uv run --with PySide6 --with pandas --with pytest pytest
tools/motor_log_viewer/tests``); skipped automatically if it isn't installed.
Runs under the Qt "offscreen" platform plugin so it needs no real display.
"""

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from tools.motor_log_viewer.tests.fixtures import write_motor_log_csv


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 not installed")
class AppCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.csv_path = write_motor_log_csv(self.directory.name, rows=40)

    def tearDown(self):
        self.directory.cleanup()

    def test_loading_a_csv_populates_every_panel(self):
        from tools.motor_log_viewer.app_state import AppState
        from tools.motor_log_viewer.application.composer import ApplicationComposer
        from PySide6.QtWidgets import QMainWindow

        window = QMainWindow()
        state = AppState()
        components = ApplicationComposer(window, state).compose()
        window.setCentralWidget(components.workspace)

        loaded = components.import_controller.load(str(self.csv_path))

        self.assertTrue(loaded)
        self.assertEqual(components.joint_table.rowCount(), 14)
        self.assertEqual(len(components.wave_panel.figure().axes), 4)  # +voltage row
        self.assertIn("fixture.csv", window.windowTitle())


if __name__ == "__main__":
    unittest.main()
