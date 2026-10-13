"""Entry point.

Run with:
  uv run --with PySide6 --with pandas python -m tools.motor_log_viewer [csv_path]
"""

import sys


def main():
    from PySide6.QtWidgets import QApplication

    from .main_window import MainWindow
    from .ui.style import APP_STYLE

    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    initial_csv = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(initial_csv=initial_csv)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
