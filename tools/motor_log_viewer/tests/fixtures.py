"""Build a tiny synthetic motor log CSV + meta.json for tests.

Plays the role of the reference project's ``benchmarks/signal_csv_fixture.py``:
a hand-rolled generator shaped exactly like the real producer
(``scripts/log_motor_data.py``) so tests never depend on a real sim run.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

JOINT_NAMES = [
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "neck_pitch",
    "head_pitch",
    "head_yaw",
    "head_roll",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
]
KT_NM_PER_A = 0.366
CURRENT_LIMIT_A = 1.75
TORQUE_LIMIT_NM = KT_NM_PER_A * CURRENT_LIMIT_A
R_OHM = 2.8114
VIN_V = 7.5
MAX_PWM = 1.0
SIM_DT = 0.005
DECIMATION = 4


def write_motor_log_csv(
    directory,
    name: str = "fixture",
    rows: int = 40,
    fell_at_s: float | None = None,
    with_voltage_model: bool = True,
) -> Path:
    """Write <directory>/<name>.csv + <name>.meta.json, log_motor_data.py-shaped."""
    directory = Path(directory)
    csv_path = directory / f"{name}.csv"
    columns = ["time", "ctrl_step"]
    for prefix in ("tau_", "vel_", "cur_", "pos_", "target_"):
        columns += [f"{prefix}{joint}" for joint in JOINT_NAMES]

    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row_index in range(rows):
            row = {
                "time": round(row_index * SIM_DT, 4),
                "ctrl_step": row_index // DECIMATION,
            }
            for joint_index, joint in enumerate(JOINT_NAMES):
                phase = 2 * math.pi * (row_index / rows) + joint_index
                tau = 0.1 * (joint_index + 1) * math.sin(phase)
                vel = 2.0 * math.cos(phase)
                row[f"tau_{joint}"] = tau
                row[f"vel_{joint}"] = vel
                row[f"cur_{joint}"] = tau / KT_NM_PER_A
                row[f"pos_{joint}"] = 0.01 * math.sin(phase)
                row[f"target_{joint}"] = 0.0
            writer.writerow(row)

    meta = {
        "policy": "fixture.onnx",
        "command": {"lin_vel_x": 0.2, "lin_vel_y": 0.0, "ang_vel_z": 0.0},
        "kt_Nm_per_A": KT_NM_PER_A,
        "current_limit_A": CURRENT_LIMIT_A,
        "torque_limit_Nm": TORQUE_LIMIT_NM,
        "sim_dt_s": SIM_DT,
        "control_dt_s": SIM_DT * DECIMATION,
        "warmup_s": 0.0,
        "fell_at_s": fell_at_s,
        "joint_names": JOINT_NAMES,
    }
    if with_voltage_model:
        meta["R_ohm"] = R_OHM
        meta["vin_V"] = VIN_V
        meta["max_pwm"] = MAX_PWM
    csv_path.with_name(f"{name}.meta.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )
    return csv_path
