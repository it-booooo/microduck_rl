"""Application-wide stylesheet, trimmed from the reference project's QSS."""

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #f0f0f0;
    color: #111111;
    font-size: 10pt;
}

QMenuBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #c4c4c4;
}

QMenuBar::item:selected {
    background-color: #d6d6d6;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #b8b8b8;
}

QTableWidget {
    background-color: #ffffff;
    gridline-color: #d8d8d8;
}

QHeaderView::section {
    background-color: #e8e8e8;
    padding: 4px;
    border: none;
    border-right: 1px solid #c4c4c4;
}

QPushButton {
    padding: 4px 12px;
}
"""
