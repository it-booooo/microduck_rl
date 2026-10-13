# Motor Log Viewer

> First time setting this up? Start with [SETUP.md](SETUP.md) -- a
> step-by-step guide (system packages, Python deps, troubleshooting) instead
> of this file's architecture tour.

A small PySide6 desktop tool for inspecting the CSVs that
`scripts/log_motor_data.py` produces (per-physical-step torque, speed,
estimated current, position, and target for all 14 joints), plus the
`.meta.json` sidecar (kt, torque limit, command, fall detection).

It intentionally copies the code architecture of
`/mnt/shared/code/2026-NCB-summer-intern` (PigBehaviorSync) -- a
composition-root `AppState`, an `ApplicationComposer` that wires
services/controllers/panels, and `data_import`/`data_export`/
`data_validation` siblings to the data layer -- scaled down from a
video-sync application with GPU-accelerated LED detection to something that
fits one small CSV. Nothing here is copy-pasted: every file is sized to what
a motor log actually needs.

## File-by-file mapping to the reference project

| This tool | Reference project | Role |
|---|---|---|
| `app_state.py` | `src/app_state.py` | Feature-grouped dataclasses; only the composition root sees `AppState` whole. |
| `application/composer.py` | `src/application/composer.py` | The one place that knows the full dependency graph. |
| `application/components.py` | `src/application/components.py` | Typed registry returned by the composer (not a service locator). |
| `application/menu_builder.py` | `src/application/menu_builder.py` | Renders `(text, callback, tooltip)` triples from each controller's `actions()`. |
| `application/session_controller.py` | `src/application/project_controller.py` | Window-title bookkeeping (dirty/save-prompt logic dropped -- this tool never edits data). |
| `data/csv_loader.py` | `src/signal_data/csv_loader.py` | Lightweight metadata parse, independent of the full dataset load. |
| `data/motor_dataset.py` | `src/signal_data/lfp_dataset.py` | Typed, joint-keyed access to one log (no chunking -- a log is a few thousand rows, not millions). |
| `data/motor_service.py` | `src/signal_data/lfp_service.py` | Thin façade over `AppState` so panels never reach into state directly. |
| `data_validation/input_checks.py` | `src/data_validation/input_checks.py` | Standalone pass over the raw file; writes a Type/File/Value report CSV. |
| `data_import/import_controller.py` | `src/data_import/import_controller.py` | Owns the "Open..." dialog, validates, then tells each panel to refresh. |
| `data_export/export_controller.py` | `src/data_export/export_controller.py` | Owns every "Export..." dialog; `ExportContext` carries its collaborators explicitly. |
| `charts/chart_helpers.py` | `src/charts/chart_helpers.py` | Wheel-zoom/drag-pan/reset -- generic Matplotlib-Qt plumbing, transfers unchanged. |
| `charts/motor_chart.py` | `src/charts/lfp_chart.py` | Pure function that (re)populates a `Figure` already owned by a canvas. |
| `ui/wave_panel.py`, `ui/joint_table.py` | `src/ui/wave_panel.py`, `src/ui/marker_table.py` | One canvas/table per panel's whole lifetime; `refresh()` redraws in place. |
| `main_window.py` | `src/main_window.py` | Owns only the Qt top-level window; everything else comes from the composer. |

## Run it

```bash
uv run --with PySide6 --with pandas python -m tools.motor_log_viewer logs/walk_vx0.20.csv
```

Omit the path and use **File > Open Motor Log CSV...**. **File > Export...**
writes the per-joint summary CSV or either chart as a PNG.

## Test it

```bash
uv run --with pandas --with pytest pytest tools/motor_log_viewer/tests
```

Data/chart/validation tests need only pandas + matplotlib (already a project
dependency). `test_app_composition.py` additionally needs PySide6 and is
skipped automatically when it isn't installed; add `--with PySide6` to run it
too (it uses the Qt `offscreen` platform plugin, so no display is required).
