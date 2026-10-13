"""Build the torque/speed/current(/voltage) time-series chart for selected joints.

Plays the role of the reference project's ``charts/lfp_chart.py``: a pure
function that (re)populates a Matplotlib ``Figure`` already owned by a Qt
(or Agg, in tests) canvas, wiring the shared pan/zoom behavior from
``chart_helpers``.
"""

from __future__ import annotations

import math

from .chart_helpers import XNavigation, install_x_navigation, resolve_plot_step

RPM_PER_RAD_S = 60.0 / (2.0 * math.pi)


def populate_motor_timeseries_figure(fig, dataset, joint_names, step=None) -> XNavigation:
    """Clear ``fig`` and redraw torque/speed/current(/voltage) panels.

    The voltage row only appears when ``dataset.has_voltage_model`` -- older
    logs (meta.json without ``R_ohm``/``vin_V``) fall back to the original
    3-row layout instead of raising.
    """
    fig.clf()
    show_voltage = dataset.has_voltage_model
    axes = fig.subplots(4 if show_voltage else 3, 1, sharex=True)
    time = dataset.time
    stride = resolve_plot_step(len(time), step)
    sliced_time = time[::stride]

    for joint in joint_names:
        axes[0].plot(sliced_time, dataset.torque(joint)[::stride], label=joint)
        axes[1].plot(
            sliced_time, dataset.speed(joint)[::stride] * RPM_PER_RAD_S, label=joint
        )
        axes[2].plot(sliced_time, dataset.current(joint)[::stride], label=joint)
        if show_voltage:
            axes[3].plot(sliced_time, dataset.voltage(joint)[::stride], label=joint)

    limit = dataset.torque_limit_Nm
    if limit:
        for sign in (1, -1):
            axes[0].axhline(sign * limit, color="red", ls="--", lw=0.8)
    if show_voltage:
        for sign in (1, -1):
            axes[3].axhline(sign * dataset.max_pwm * dataset.vin_V, color="red", ls="--", lw=0.8)

    axes[0].set_ylabel("Torque [N·m]")
    axes[1].set_ylabel("Speed [rpm]")
    axes[2].set_ylabel("Est. current [A]")
    if show_voltage:
        axes[3].set_ylabel("Est. voltage [V]")
    axes[-1].set_xlabel("Time [s]")
    if joint_names:
        axes[0].legend(ncol=min(len(joint_names), 5), fontsize=8, loc="upper right")
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.tight_layout()

    full_xlim = (
        (float(sliced_time[0]), float(sliced_time[-1]))
        if len(sliced_time) > 1
        else (0.0, 1.0)
    )
    # axes share x (sharex=True), so navigating axes[0] moves every row.
    return install_x_navigation(fig, axes[0], full_xlim)
