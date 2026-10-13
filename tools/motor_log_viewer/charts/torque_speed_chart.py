"""Build one joint's torque-vs-speed scatter plot (sim2real headroom check).

Static (no pan/zoom) -- same role as the reference project's smaller
secondary charts that don't need interactive navigation.
"""

from __future__ import annotations

import math

RPM_PER_RAD_S = 60.0 / (2.0 * math.pi)


def populate_torque_speed_figure(fig, dataset, joint: str):
    """Clear ``fig`` and redraw the torque-vs-speed scatter for one joint."""
    fig.clf()
    ax = fig.add_subplot()
    limit = dataset.torque_limit_Nm

    ax.scatter(dataset.speed(joint) * RPM_PER_RAD_S, dataset.torque(joint), s=4, alpha=0.3)
    if limit:
        ax.axhline(limit, color="red", ls="--", lw=0.8)
        ax.axhline(-limit, color="red", ls="--", lw=0.8)
    ax.set_title(joint, fontsize=11)
    ax.set_xlabel("Speed [rpm]")
    ax.set_ylabel("Torque [N·m]")
    ax.grid(alpha=0.3)
    fig.tight_layout()
