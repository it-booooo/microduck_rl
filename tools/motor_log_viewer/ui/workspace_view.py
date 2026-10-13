"""Arrange the joint table, wave panel, and torque-speed panel in one widget.

Plays the role of the reference project's ``WorkspaceView``: a dumb layout
container the composer hands fully-built panels to.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter


class WorkspaceView(QSplitter):
    """Left: per-joint summary table. Right: time-series over torque-speed."""

    def __init__(self, joint_table, wave_panel, torque_speed_panel):
        super().__init__(Qt.Orientation.Horizontal)
        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(wave_panel)
        right.addWidget(torque_speed_panel)
        right.setSizes([500, 500])

        self.addWidget(joint_table)
        self.addWidget(right)
        self.setSizes([350, 1050])
