#!/usr/bin/env python3
"""分析 log_motor_data.py 產生的 CSV:統計表、時序圖、轉矩–轉速圖。

用法(於 microduck_rl 根目錄):
  uv run --with pandas --with matplotlib scripts/analyze_motor_log.py logs/walk_vx0.20.csv

輸出到 <csv 檔名>_report/:
  summary.csv          各關節統計(依 RMS 轉矩排序)
  timeseries.png       指定關節的轉矩、轉速、估計電流時序
  torque_speed.png     14 顆馬達的轉矩–轉速工作點
  torque_bars.png      各關節 RMS 與峰值轉矩長條圖
"""
import argparse
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RPM = 60.0 / (2.0 * math.pi)


def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def main():
    p = argparse.ArgumentParser(description="分析馬達轉矩／轉速記錄")
    p.add_argument("csv", help="log_motor_data.py 產生的 CSV")
    p.add_argument("--joints", nargs="*", default=None,
                   help="時序圖要畫的關節名稱(預設:名稱以 left 開頭的關節)")
    p.add_argument("--seconds", type=float, default=3.0, help="時序圖顯示的秒數")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    base = os.path.splitext(args.csv)[0]
    meta = {}
    if os.path.exists(base + ".meta.json"):
        with open(base + ".meta.json", encoding="utf-8") as f:
            meta = json.load(f)
    names = meta.get("joint_names") or [c[4:] for c in df.columns if c.startswith("tau_")]
    tlim = meta.get("torque_limit_Nm")
    out_dir = base + "_report"
    os.makedirs(out_dir, exist_ok=True)

    # ---- 1. 統計表 ----
    stats = []
    for n in names:
        tau = df[f"tau_{n}"].to_numpy()
        vel = df[f"vel_{n}"].to_numpy()
        cur = df[f"cur_{n}"].to_numpy()
        power = tau * vel
        stats.append({
            "joint": n,
            "tau_rms_Nm": rms(tau),
            "tau_peak_Nm": float(np.max(np.abs(tau))),
            "speed_rms_rpm": rms(vel) * RPM,
            "speed_peak_rpm": float(np.max(np.abs(vel))) * RPM,
            "current_rms_A": rms(cur),
            "current_peak_A": float(np.max(np.abs(cur))),
            "power_abs_mean_W": float(np.mean(np.abs(power))),
            "power_peak_W": float(np.max(np.abs(power))),
            "time_at_limit_pct": (float(np.mean(np.abs(tau) >= 0.98 * tlim)) * 100.0
                                  if tlim else float("nan")),
        })
    st = pd.DataFrame(stats).sort_values("tau_rms_Nm", ascending=False)
    st.to_csv(os.path.join(out_dir, "summary.csv"), index=False, float_format="%.4f")
    print(st.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # ---- 2. 時序圖 ----
    joints = args.joints or [n for n in names if n.startswith("left")] or names[:5]
    t0 = df["time"].iloc[0]
    seg = df[df["time"] <= t0 + args.seconds]
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for n in joints:
        axes[0].plot(seg["time"], seg[f"tau_{n}"], label=n)
        axes[1].plot(seg["time"], seg[f"vel_{n}"] * RPM, label=n)
        axes[2].plot(seg["time"], seg[f"cur_{n}"], label=n)
    if tlim:
        for s in (1, -1):
            axes[0].axhline(s * tlim, color="red", ls="--", lw=0.8)
    axes[0].set_ylabel("Torque [N·m]")
    axes[1].set_ylabel("Speed [rpm]")
    axes[2].set_ylabel("Est. current [A]")
    axes[2].set_xlabel("Time [s]")
    axes[0].legend(ncol=min(len(joints), 5), fontsize=8, loc="upper right")
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "timeseries.png"), dpi=150)
    plt.close(fig)

    # ---- 3. 轉矩–轉速工作點 ----
    cols = 4
    rows_n = math.ceil(len(names) / cols)
    fig, axes = plt.subplots(rows_n, cols, figsize=(4 * cols, 3.2 * rows_n), squeeze=False)
    for idx, n in enumerate(names):
        ax = axes[idx // cols][idx % cols]
        ax.scatter(df[f"vel_{n}"] * RPM, df[f"tau_{n}"], s=2, alpha=0.3)
        if tlim:
            ax.axhline(tlim, color="red", ls="--", lw=0.8)
            ax.axhline(-tlim, color="red", ls="--", lw=0.8)
        ax.set_title(n, fontsize=9)
        ax.set_xlabel("Speed [rpm]", fontsize=8)
        ax.set_ylabel("Torque [N·m]", fontsize=8)
        ax.grid(alpha=0.3)
    for idx in range(len(names), rows_n * cols):
        axes[idx // cols][idx % cols].axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "torque_speed.png"), dpi=150)
    plt.close(fig)

    # ---- 4. 轉矩長條圖 ----
    order = st["joint"].tolist()
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.bar(x - 0.2, st["tau_rms_Nm"], width=0.4, label="RMS")
    ax.bar(x + 0.2, st["tau_peak_Nm"], width=0.4, label="Peak |τ|")
    if tlim:
        ax.axhline(tlim, color="red", ls="--", lw=0.8, label="Torque limit")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Torque [N·m]")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "torque_bars.png"), dpi=150)
    plt.close(fig)

    print(f"\n報表已輸出到 {out_dir}/")


if __name__ == "__main__":
    main()
