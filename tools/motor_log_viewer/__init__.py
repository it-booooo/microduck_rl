"""Desktop viewer for scripts/log_motor_data.py CSVs.

Package layout mirrors /mnt/shared/code/2026-NCB-summer-intern (PigBehaviorSync):
a composition-root AppState split by feature, an ApplicationComposer that wires
services/controllers/panels together, thin data-access services that hide
AppState from the UI, and data_import/data_export/data_validation siblings to
signal_data. See tools/motor_log_viewer/README.md for the file-by-file mapping.
"""
