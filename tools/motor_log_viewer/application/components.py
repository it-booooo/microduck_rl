"""The constructed application object graph.

This is a typed registry, not a service locator: only the composition root
receives the complete object; feature controllers receive explicit fields.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApplicationComponents:
    motor_service: object
    joint_table: object
    wave_panel: object
    torque_speed_panel: object
    workspace: object
    session_controller: object
    import_controller: object
    export_controller: object
