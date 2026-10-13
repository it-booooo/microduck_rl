"""Embeds the torque-vs-speed scatter plot, one joint at a time via a dropdown."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..charts.torque_speed_chart import populate_torque_speed_figure


class TorqueSpeedPanel(QWidget):
    """Static sim2real headroom check for one joint, picked from a dropdown.

    The dropdown is populated heaviest-RMS-torque-joint first, same order as
    ``JointTable``'s default sort, so the joint most worth looking at is the
    one shown first.
    """

    def __init__(self, motor_service):
        super().__init__()
        self.motor_service = motor_service

        self.joint_combo = QComboBox()
        self.joint_combo.currentTextChanged.connect(self._on_joint_changed)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Joint:"))
        controls.addWidget(self.joint_combo, stretch=1)
        controls.addWidget(refresh_button)

        self.canvas = FigureCanvasQTAgg(Figure())

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.canvas, stretch=1)

    def figure(self):
        return self.canvas.figure

    def _on_joint_changed(self, joint: str) -> None:
        if not joint:
            return
        populate_torque_speed_figure(self.canvas.figure, self.motor_service.dataset(), joint)
        self.canvas.draw_idle()

    def refresh(self) -> None:
        dataset = self.motor_service.dataset()
        if self.joint_combo.count() == 0:
            ordered_joints = [stats.joint for stats in self.motor_service.summary()]
            self.joint_combo.blockSignals(True)
            self.joint_combo.addItems(ordered_joints)
            self.joint_combo.blockSignals(False)

        joint = self.joint_combo.currentText() or dataset.joint_names[0]
        populate_torque_speed_figure(self.canvas.figure, dataset, joint)
        self.canvas.draw_idle()
