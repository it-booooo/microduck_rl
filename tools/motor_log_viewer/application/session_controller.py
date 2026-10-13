"""Own the window title: reflects the currently loaded motor log, if any.

Scaled-down analogue of the reference project's ``ProjectController`` -- no
dirty-state/save-prompt concept applies here (this tool never edits data),
so only the title-tracking half survives.
"""

from __future__ import annotations


class SessionController:
    APPLICATION_TITLE = "Microduck Motor Log Viewer"

    def __init__(self, parent, session_state):
        self.parent = parent
        self.session_state = session_state

    def set_loaded_path(self, path: str) -> None:
        self.session_state.loaded_path = path
        self.update_title()

    def update_title(self) -> None:
        self.parent.setWindowTitle(
            f"{self.session_state.display_name} - {self.APPLICATION_TITLE}"
        )
