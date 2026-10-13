"""Per-joint summary table, sortable by any column.

Plays the role of the reference project's ``MarkerTable``: a thin Qt widget
over one service method, re-populated wholesale on ``refresh()`` rather than
diffed in place -- the dataset is small enough that this is simplest.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

COLUMNS = [
    ("joint", "Joint"),
    ("tau_rms_Nm", "RMS τ [N·m]"),
    ("tau_peak_Nm", "Peak τ [N·m]"),
    ("speed_peak_rpm", "Peak speed [rpm]"),
    ("current_rms_A", "RMS I [A]"),
    ("time_at_limit_pct", "At limit [%]"),
    ("voltage_peak_V", "Peak V [V]"),
    ("time_voltage_saturated_pct", "V sat [%]"),
]


class JointTable(QTableWidget):
    """Shows ``MotorAnalysisService.summary()``, heaviest-load joint first."""

    def __init__(self, motor_service):
        super().__init__()
        self.motor_service = motor_service
        self.setColumnCount(len(COLUMNS))
        self.setHorizontalHeaderLabels([label for _, label in COLUMNS])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)

    def refresh(self) -> None:
        rows = self.motor_service.summary()
        self.setSortingEnabled(False)
        self.setRowCount(len(rows))
        for row_index, stats in enumerate(rows):
            for col_index, (field, _label) in enumerate(COLUMNS):
                value = getattr(stats, field)
                item = QTableWidgetItem()
                if isinstance(value, str):
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                else:
                    item.setData(Qt.ItemDataRole.DisplayRole, round(float(value), 4))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.setItem(row_index, col_index, item)
        self.setSortingEnabled(True)
        self.resizeColumnsToContents()
