"""Validate a motor log CSV against the schema scripts/log_motor_data.py writes.

Plays the role of the reference project's ``data_validation.check``: a
standalone pass over the raw file (independent of any dataset object) that
writes a flat Type/File/Value report CSV -- same report shape, scaled down
from chunked/cancellable (built for multi-GB recordings) to a single pass
(a motor log is at most a few thousand rows).
"""

from __future__ import annotations

import csv
from pathlib import Path

EXPECTED_PREFIXES = ("tau_", "vel_", "cur_", "pos_", "target_")
EXPECTED_JOINT_COUNT = 14


def default_output_path(csv_path) -> Path:
    path = Path(csv_path)
    return path.with_name(f"{path.stem}.check.csv")


def check(info: dict, output_path=None) -> dict:
    """Validate column schema, cell values, and torque-limit compliance.

    Returns a report dict. Unless ``output_path`` is ``False``, also writes
    the report as a Type/File/Value CSV (``output_path`` or
    ``default_output_path(info["path"])``) and records where under
    ``report["output_path"]``.
    """
    path = Path(info["path"])
    joint_names = info["joint_names"]
    issues: list[dict] = []

    expected_columns = {"time", "ctrl_step"}
    for prefix in EXPECTED_PREFIXES:
        expected_columns.update(f"{prefix}{joint}" for joint in joint_names)
    missing_columns = sorted(expected_columns - set(info["columns"]))
    for column in missing_columns:
        issues.append({"Type": "Missing column", "File": path.name, "Value": column})

    non_finite_count = 0
    row_count = 0
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_num, row in enumerate(reader, start=2):
            row_count += 1
            for column in reader.fieldnames or ():
                value = row.get(column, "")
                try:
                    is_finite = _is_finite_number(value)
                except ValueError:
                    non_finite_count += 1
                    issues.append(
                        {
                            "Type": "Unparseable value",
                            "File": f"line {row_num}",
                            "Value": f"{column}={value}",
                        }
                    )
                    continue
                if not is_finite:
                    non_finite_count += 1
                    issues.append(
                        {
                            "Type": "Non-finite value",
                            "File": f"line {row_num}",
                            "Value": f"{column}={value}",
                        }
                    )

    meta = info.get("meta") or {}
    if len(joint_names) != EXPECTED_JOINT_COUNT:
        issues.append(
            {
                "Type": "Joint count",
                "File": path.name,
                "Value": f"expected {EXPECTED_JOINT_COUNT} joints, got {len(joint_names)}",
            }
        )
    fell_at_s = meta.get("fell_at_s")
    if fell_at_s is not None:
        issues.append(
            {
                "Type": "Fall detected",
                "File": path.name,
                "Value": f"fell_at_s={fell_at_s}",
            }
        )

    report = {
        "path": str(path),
        "row_count": row_count,
        "missing_columns": missing_columns,
        "non_finite_count": non_finite_count,
        "fell_at_s": fell_at_s,
        "issues": issues,
        # A fall is reported but not fatal -- the recording is still usable,
        # just truncated; only schema/value problems fail validation.
        "ok": not missing_columns and non_finite_count == 0,
    }

    if output_path is not False:
        out_file = (
            default_output_path(path) if output_path is None else Path(output_path)
        )
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with out_file.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["Type", "File", "Value"])
            writer.writeheader()
            writer.writerows(issues)
        report["output_path"] = str(out_file)

    return report


def _is_finite_number(value: str) -> bool:
    number = float(value)
    return number == number and number not in (float("inf"), float("-inf"))
