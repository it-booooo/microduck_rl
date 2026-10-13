"""Export menu actions: summary CSV and the currently shown charts.

Plays the role of the reference project's ``data_export.ExportController``:
an explicit ``ExportContext`` carries every collaborator it needs, and
``actions()`` hands the menu builder (text, callback, tooltip) triples
without the menu layer knowing what export means.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QFileDialog, QMessageBox

from .file_writers import write_figure_png, write_summary_csv


@dataclass
class ExportContext:
    parent: object
    motor_service: object
    wave_panel: object
    torque_speed_panel: object


class ExportController:
    def __init__(self, context: ExportContext):
        self.context = context

    def actions(self):
        return [
            (
                "Export Summary CSV...",
                self.export_summary,
                "Per-joint RMS/peak torque, speed, and current.",
            ),
            (
                "Export Time-Series Chart...",
                self.export_wave_chart,
                "The currently displayed torque/speed/current plot.",
            ),
            (
                "Export Torque-Speed Chart...",
                self.export_torque_speed_chart,
                "The 14-joint torque-vs-speed scatter grid.",
            ),
        ]

    def export_summary(self) -> bool:
        context = self.context
        try:
            rows = context.motor_service.summary()
        except ValueError as error:
            QMessageBox.warning(context.parent, "Export Summary CSV", str(error))
            return False
        path, _ = QFileDialog.getSaveFileName(
            context.parent, "Export Summary CSV", "summary.csv", "CSV Files (*.csv)"
        )
        if not path:
            return False
        write_summary_csv(rows, path)
        return True

    def export_wave_chart(self) -> bool:
        return self._export_figure(
            self.context.wave_panel.figure(),
            "timeseries.png",
            "Export Time-Series Chart",
        )

    def export_torque_speed_chart(self) -> bool:
        return self._export_figure(
            self.context.torque_speed_panel.figure(),
            "torque_speed.png",
            "Export Torque-Speed Chart",
        )

    def _export_figure(self, figure, default_name: str, title: str) -> bool:
        if figure is None or not figure.axes:
            QMessageBox.warning(self.context.parent, title, "Please open a motor log CSV first.")
            return False
        path, _ = QFileDialog.getSaveFileName(
            self.context.parent, title, default_name, "PNG Files (*.png)"
        )
        if not path:
            return False
        write_figure_png(figure, path)
        return True
