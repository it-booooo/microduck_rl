"""Construct and wire the application object graph.

Plays the role of the reference project's ``ApplicationComposer``: the only
place that knows the full dependency graph, so every other module only ever
sees the collaborators its constructor asks for.
"""

from __future__ import annotations

from ..data.motor_service import MotorAnalysisService
from ..data_export.export_controller import ExportContext, ExportController
from ..data_import.import_controller import ImportContext, ImportController
from ..ui.joint_table import JointTable
from ..ui.torque_speed_panel import TorqueSpeedPanel
from ..ui.wave_panel import WavePanel
from ..ui.workspace_view import WorkspaceView
from .components import ApplicationComponents
from .menu_builder import MenuBuilder
from .session_controller import SessionController


class ApplicationComposer:
    """Construct and wire the application object graph."""

    def __init__(self, window, app_state):
        self.window = window
        self.app_state = app_state

    def compose(self) -> ApplicationComponents:
        state = self.app_state
        motor_service = MotorAnalysisService(state.data, state.analysis)

        joint_table = JointTable(motor_service)
        wave_panel = WavePanel(motor_service, state.data)
        torque_speed_panel = TorqueSpeedPanel(motor_service)
        workspace = WorkspaceView(joint_table, wave_panel, torque_speed_panel)

        session_controller = SessionController(self.window, state.session)

        import_context = ImportContext(
            parent=self.window,
            session_controller=session_controller,
            joint_table=joint_table,
            wave_panel=wave_panel,
            torque_speed_panel=torque_speed_panel,
        )
        export_context = ExportContext(
            parent=self.window,
            motor_service=motor_service,
            wave_panel=wave_panel,
            torque_speed_panel=torque_speed_panel,
        )
        import_controller = ImportController(import_context, state)
        export_controller = ExportController(export_context)

        components = ApplicationComponents(
            motor_service=motor_service,
            joint_table=joint_table,
            wave_panel=wave_panel,
            torque_speed_panel=torque_speed_panel,
            workspace=workspace,
            session_controller=session_controller,
            import_controller=import_controller,
            export_controller=export_controller,
        )

        MenuBuilder(
            window=self.window,
            import_controller=import_controller,
            export_controller=export_controller,
        ).build()
        return components
