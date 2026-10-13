"""Application state grouped by feature ownership.

The dataclasses in this module contain shared data only. Qt widgets and
controllers receive the specific state objects they need through their
constructors, same split as the reference project's ``src/app_state.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data.motor_dataset import MotorLogDataset


@dataclass
class DataState:
    """The currently loaded motor log and the joints selected for plotting."""

    dataset: "MotorLogDataset | None" = None
    source_path: str | None = None
    selected_joints: list[str] = field(default_factory=list)

    @property
    def joint_names(self) -> list[str]:
        dataset = self.dataset
        return [] if dataset is None else dataset.joint_names


@dataclass
class AnalysisSettings:
    """User-adjustable analysis parameters shared by the summary table."""

    # Fraction of torque_limit_Nm a sample must reach to count as "at limit"
    # in JointStats.time_at_limit_pct -- matches analyze_motor_log.py's 0.98.
    near_limit_fraction: float = 0.98


@dataclass
class SessionState:
    """Currently loaded file, for window-title bookkeeping."""

    loaded_path: str | None = None

    @property
    def display_name(self) -> str:
        return Path(self.loaded_path).name if self.loaded_path else "No log loaded"


@dataclass
class AppState:
    """Composition root for all feature states.

    Only the application root should normally receive this complete object.
    Child components are injected with one or more feature-specific states.
    """

    data: DataState = field(default_factory=DataState)
    analysis: AnalysisSettings = field(default_factory=AnalysisSettings)
    session: SessionState = field(default_factory=SessionState)
