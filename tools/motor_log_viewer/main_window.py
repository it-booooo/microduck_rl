"""Application shell.

Feature construction, signal wiring, and menus live in dedicated
collaborators assembled by ``ApplicationComposer`` -- this class only owns
the Qt top-level window, same split as the reference project's
``src/main_window.py``.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from .app_state import AppState
from .application.composer import ApplicationComposer


class MainWindow(QMainWindow):
    def __init__(self, app_state=None, initial_csv: str | None = None):
        super().__init__()
        self.app_state = app_state or AppState()
        self.resize(1400, 820)
        self.setMinimumSize(1100, 640)

        self.components = ApplicationComposer(self, self.app_state).compose()
        self.setCentralWidget(self.components.workspace)
        self.components.session_controller.update_title()

        if initial_csv:
            self.components.import_controller.load(initial_csv)
