#!/usr/bin/env python3
"""無畫面執行 ONNX 策略,記錄 14 顆馬達的轉矩、轉速、估計電流(每個物理步,200 Hz)。

放在 microduck_rl/scripts/ 底下,於 repo 根目錄執行:
  uv run scripts/log_motor_data.py --walking policies/velstand.onnx --new-cmd-obs \
      --lin-vel-x 0.2 --duration 12 --out logs/walk_vx0.20.csv

輸出:
  <out>.csv        每列一個物理步(5 ms),欄位 time, ctrl_step, tau_*, vel_*, cur_*, pos_*, target_*
  <out>.meta.json  kt、轉矩上限、指令、策略路徑、關節名稱等設定
"""
import argparse
import csv
import json
import math
import os

import mujoco
import numpy as np

from infer_policy import MICRODUCK_XML, PolicyInference

FALL_HEIGHT = 0.07   # 軀幹高度低於此值(m)視為跌倒,停止記錄
DECIMATION = 4       # 與 infer_policy.py 相同:5 ms × 4 = 20 ms(50 Hz 控制)
SIM_DT = 0.005


def main():
    p = argparse.ArgumentParser(description="記錄 Microduck 各馬達的轉矩、轉速與估計電流")
    p.add_argument("--walking", required=True, help="walking 策略 ONNX 路徑")
    p.add_argument("--standing", default=None, help="(選用)standing 策略 ONNX 路徑")
    p.add_argument("--new-cmd-obs", action="store_true", help="61 維觀測的策略必須加上")
    p.add_argument("--lin-vel-x", type=float, default=0.2, help="前進速度指令 m/s(訓練範圍約 ±0.3)")
    p.add_argument("--lin-vel-y", type=float, default=0.0, help="側移速度指令 m/s(約 ±0.2)")
    p.add_argument("--ang-vel-z", type=float, default=0.0, help="轉向角速度指令 rad/s(約 ±1.5)")
    p.add_argument("--duration", type=float, default=12.0, help="總模擬秒數")
    p.add_argument("--warmup", type=float, default=2.0, help="開頭捨棄的秒數(起步暫態)")
    p.add_argument("--action-scale", type=float, default=1.0, help="須與訓練時一致")
    p.add_argument("--current-limit", type=float, default=1.75,
                   help="XL330 韌體電流上限 [A],轉矩截斷在 ±kt×此值;<=0 關閉")
    p.add_argument("--out", default="logs/motor_log.csv", help="輸出 CSV 路徑")
    args = p.parse_args()

    # ---- 模型與致動器設定(與 infer_policy.py 相同) ----
    model = mujoco.MjModel.from_xml_path(MICRODUCK_XML)
    model.opt.timestep = SIM_DT
    data = mujoco.MjData(model)

    from bam.model import load_model
    bam_model = load_model(motor_name="xl330", model="m6")
    kt = float(bam_model.kt.value)
    winding_r = float(bam_model.R.value)
    supply_voltage = float(bam_model.actuator.vin)
    max_pwm = float(bam_model.actuator.max_pwm)
    torque_limit = None
    if args.current_limit > 0:
        torque_limit = kt * args.current_limit
        model.actuator_forcerange[:, 0] = -torque_limit
        model.actuator_forcerange[:, 1] = torque_limit
        model.actuator_forcelimited[:] = 1

    gears = model.actuator_gear[:, 0]
    if not np.allclose(gears, 1.0):
        print(f"警告:致動器 gear 不全為 1({gears}),關節轉矩 = gear × actuator_force")

    policy = PolicyInference(
        model, data,
        walking_onnx_path=args.walking,
        standing_onnx_path=args.standing,
        action_scale=args.action_scale,
        use_projected_gravity=True,
        new_cmd_obs=args.new_cmd_obs,
    )

    # ---- 初始姿態 ----
    fj = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "trunk_base_freejoint")
    qadr = int(model.jnt_qposadr[fj])
    data.qpos[qadr:qadr + 3] = [0.0, 0.0, 0.125]
    data.qpos[qadr + 3:qadr + 7] = [1, 0, 0, 0]
    for i, qi in enumerate(policy.joint_qpos_indices):
        data.qpos[qi] = policy.default_pose[i]
    data.ctrl[:] = policy.default_pose
    mujoco.mj_forward(model, data)

    # ---- 觀測維度檢查 ----
    obs_len = policy.get_observations().size
    onnx_len = policy.walking_session.get_inputs()[0].shape[-1]
    if isinstance(onnx_len, int) and onnx_len != obs_len:
        raise SystemExit(
            f"觀測維度不符:ONNX 需要 {onnx_len},目前產生 {obs_len}。"
            f"{'請加上 --new-cmd-obs' if onnx_len == 61 else '請移除 --new-cmd-obs'}")

    policy.set_vel_cmd(args.lin_vel_x, args.lin_vel_y, args.ang_vel_z)

    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"m{i}"
             for i in range(model.nu)]
    qv = policy.joint_qvel_indices
    qp = policy.joint_qpos_indices

    # ---- 模擬與記錄 ----
    n_ctrl = int(round(args.duration / (DECIMATION * SIM_DT)))
    rows = []
    fell_at = None
    for k in range(n_ctrl):
        action = policy.infer()
        policy.apply_action(action)
        for _ in range(DECIMATION):
            mujoco.mj_step(model, data)
            if data.time < args.warmup:
                continue
            tau = data.actuator_force.copy()
            vel = data.qvel[qv].copy()
            pos = data.qpos[qp].copy()
            row = {"time": round(float(data.time), 4), "ctrl_step": k}
            for i, n in enumerate(names):
                row[f"tau_{n}"] = float(tau[i])
            for i, n in enumerate(names):
                row[f"vel_{n}"] = float(vel[i])
            for i, n in enumerate(names):
                row[f"cur_{n}"] = float(tau[i] / kt)
            for i, n in enumerate(names):
                row[f"pos_{n}"] = float(pos[i])
            for i, n in enumerate(names):
                row[f"target_{n}"] = float(data.ctrl[i])
            rows.append(row)
        if data.qpos[qadr + 2] < FALL_HEIGHT:
            fell_at = float(data.time)
            print(f"警告:機器人在 t = {fell_at:.2f} s 跌倒,提前停止記錄")
            break

    if not rows:
        raise SystemExit("沒有記錄到任何資料:請確認 --duration 大於 --warmup,且機器人沒有在暖機期間跌倒")

    # ---- 存檔 ----
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    meta = {
        "policy": args.walking,
        "command": {"lin_vel_x": args.lin_vel_x, "lin_vel_y": args.lin_vel_y,
                    "ang_vel_z": args.ang_vel_z},
        "kt_Nm_per_A": kt,
        "current_limit_A": args.current_limit,
        "torque_limit_Nm": torque_limit,
        # DC motor constants (XL330 M6 BAM model) for terminal-voltage /
        # duty-cycle estimation: V = I*R + kt*dq, duty = V/vin.
        "R_ohm": winding_r,
        "vin_V": supply_voltage,
        "max_pwm": max_pwm,
        "sim_dt_s": SIM_DT,
        "control_dt_s": SIM_DT * DECIMATION,
        "warmup_s": args.warmup,
        "fell_at_s": fell_at,
        "joint_names": names,
    }
    meta_path = os.path.splitext(args.out)[0] + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # ---- 終端摘要 ----
    rpm = 60.0 / (2.0 * math.pi)
    print(f"\n已存 {len(rows)} 列({len(rows) * SIM_DT:.1f} s)到 {args.out}")
    print(f"設定檔:{meta_path}   kt = {kt:.4f} N·m/A   轉矩上限 = {torque_limit}")
    print(f"\n{'關節':<16}{'RMS 轉矩 N·m':>14}{'峰值轉矩 N·m':>14}{'峰值轉速 rpm':>14}{'RMS 電流 A':>12}")
    for n in names:
        t = np.array([r[f"tau_{n}"] for r in rows])
        v = np.array([r[f"vel_{n}"] for r in rows])
        print(f"{n:<16}{np.sqrt(np.mean(t ** 2)):>14.4f}{np.max(np.abs(t)):>14.4f}"
              f"{np.max(np.abs(v)) * rpm:>14.1f}{np.sqrt(np.mean(t ** 2)) / kt:>12.3f}")


if __name__ == "__main__":
    main()
