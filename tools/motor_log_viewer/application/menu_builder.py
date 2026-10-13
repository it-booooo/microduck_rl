"""Build the File menu from the import/export controllers' own action lists.

Plays the role of the reference project's ``MenuBuilder``: the menu layer
never hardcodes what "import" or "export" means -- it just renders whatever
``(text, callback, tooltip)`` triples each controller's ``actions()`` returns.
"""

from __future__ import annotations

from PySide6.QtGui import QAction


class MenuBuilder:
    def __init__(self, *, window, import_controller, export_controller):
        self.window = window
        self.import_controller = import_controller
        self.export_controller = export_controller

    def build(self) -> None:
        file_menu = self.window.menuBar().addMenu("File")
        for text, callback, tooltip in self.import_controller.actions():
            self._add_action(file_menu, text, callback, tooltip)
        file_menu.addSeparator()
        for text, callback, tooltip in self.export_controller.actions():
            self._add_action(file_menu, text, callback, tooltip)
        file_menu.addSeparator()
        self._add_action(file_menu, "Exit", self.window.close)

    def _add_action(self, menu, text, callback, tooltip=None) -> None:
        action = QAction(text, self.window)
        if tooltip:
            action.setToolTip(tooltip)
        action.triggered.connect(callback)
        menu.addAction(action)
