"""The "Open Motor Log CSV..." action: load, validate, and notify panels.

Plays the role of the reference project's ``data_import.ImportController``:
owns the file dialog, runs validation before committing the new dataset to
``AppState``, and then tells each panel to refresh -- panels never poll
AppState themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..data.csv_loader import parse_motor_log_info
from ..data.motor_dataset import MotorLogDataset
from ..data_validation.input_checks import check


@dataclass
class ImportContext:
    parent: object
    session_controller: object
    joint_table: object
    wave_panel: object
    torque_speed_panel: object


class ImportController:
    def __init__(self, context: ImportContext, app_state):
        self.context = context
        self.app_state = app_state

    def actions(self):
        return [
            (
                "Open Motor Log CSV...",
                self.open_csv,
                "Load a log_motor_data.py CSV + its .meta.json sidecar.",
            )
        ]

    def open_csv(self) -> bool:
        path, _ = QFileDialog.getOpenFileName(
            self.context.parent, "Open Motor Log CSV", "logs", "CSV Files (*.csv)"
        )
        if not path:
            return False
        return self.load(path)

    def load(self, path: str) -> bool:
        """Load ``path``, prompting past validation issues rather than hiding them."""
        info = parse_motor_log_info(path)
        report = check(info)
        if not report["ok"]:
            choice = QMessageBox.warning(
                self.context.parent,
                "Motor Log Validation",
                f"{path} failed validation "
                f"({report['non_finite_count']} non-finite value(s), "
                f"missing columns: {report['missing_columns']}).\n"
                f"Report written to {report.get('output_path')}.\n\nLoad anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return False

        dataset = MotorLogDataset.from_csv(info)
        state = self.app_state.data
        state.dataset = dataset
        state.source_path = path
        state.selected_joints = dataset.joint_names[:5]

        self.context.session_controller.set_loaded_path(path)
        self.context.joint_table.refresh()
        self.context.wave_panel.refresh()
        self.context.torque_speed_panel.refresh()
        return True
