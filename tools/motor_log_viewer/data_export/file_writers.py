"""Small file-writing helpers shared by the export controller."""

from __future__ import annotations

import csv
from pathlib import Path

from ..data.motor_dataset import JointStats

SUMMARY_FIELDS = [
    "joint",
    "tau_rms_Nm",
    "tau_peak_Nm",
    "speed_rms_rpm",
    "speed_peak_rpm",
    "current_rms_A",
    "current_peak_A",
    "power_abs_mean_W",
    "power_peak_W",
    "time_at_limit_pct",
    "voltage_rms_V",
    "voltage_peak_V",
    "time_voltage_saturated_pct",
]


def write_summary_csv(rows: list[JointStats], path) -> Path:
    """Write per-joint statistics, one row per joint, to a CSV file."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: getattr(row, field) for field in SUMMARY_FIELDS})
    return out_path


def write_figure_png(fig, path) -> Path:
    """Save a Matplotlib figure as a PNG."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    return out_path
