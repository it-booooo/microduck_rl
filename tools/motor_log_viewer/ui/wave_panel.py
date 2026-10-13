"""Embeds the time-series chart with a joint picker.

Plays the role of the reference project's ``WavePanel``: owns one canvas for
its whole lifetime (``populate_*`` clears and redraws it in place) instead of
rebuilding a new Figure/canvas pair per refresh, so pan/zoom state and the
callback registry installed by ``install_x_navigation`` stay valid.
"""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..charts.motor_chart import populate_motor_timeseries_figure


class WavePanel(QWidget):
    """Torque/speed/current time-series for a user-chosen subset of joints."""

    joints_changed = Signal(list)

    def __init__(self, motor_service, data_state):
        super().__init__()
        self.motor_service = motor_service
        self.data_state = data_state

        self.joint_list = QListWidget()
        self.joint_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self.joint_list.itemSelectionChanged.connect(self._on_selection_changed)

        redraw_button = QPushButton("Redraw")
        redraw_button.clicked.connect(self.refresh)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Joints (ctrl/cmd-click to multi-select):"))
        controls.addWidget(self.joint_list, stretch=1)
        controls.addWidget(redraw_button)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(11, 8)))

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.canvas, stretch=1)

    def figure(self):
        return self.canvas.figure

    def _on_selection_changed(self) -> None:
        selected = [item.text() for item in self.joint_list.selectedItems()]
        if selected:
            self.data_state.selected_joints = selected
            self.joints_changed.emit(selected)

    def refresh(self) -> None:
        dataset = self.motor_service.dataset()
        if self.joint_list.count() == 0:
            self.joint_list.blockSignals(True)
            self.joint_list.addItems(dataset.joint_names)
            preselected = set(self.motor_service.selected_joints())
            for row in range(self.joint_list.count()):
                item = self.joint_list.item(row)
                item.setSelected(item.text() in preselected)
            self.joint_list.blockSignals(False)

        joints = [
            item.text() for item in self.joint_list.selectedItems()
        ] or dataset.joint_names[:5]
        populate_motor_timeseries_figure(self.canvas.figure, dataset, joints)
        self.canvas.draw_idle()
