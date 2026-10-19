"""Centralized visual tokens and Qt stylesheet."""
STYLESHEET = '''
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #243249; }
QMainWindow, QWidget#root { background: #f3f5fa; }
QFrame#card { background: #ffffff; border: 1px solid #e2e7f0; border-radius: 16px; }
QLabel { background: transparent; border: none; }
QLabel#brand { font-size: 26px; font-weight: 800; color: #192b49; }
QLabel#title { font-size: 24px; font-weight: 700; color: #192b49; }
QLabel#section { font-size: 16px; font-weight: 700; }
QLabel#muted { color: #66758b; }
QLabel#badge { color: #18765e; background: #e4f4ed; padding: 7px 12px; border-radius: 12px; font-weight: 600; }
QLabel#step { color: #5667b1; font-size: 11px; font-weight: 700; }
QPushButton { background: #ffffff; border: 1px solid #dbe1ed; border-radius: 9px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #eef2ff; border-color: #a5b4ed; }
QPushButton:pressed { background: #e1e7fd; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus { border: 2px solid #6275dc; }
QPushButton#primary { background: #5365d9; color: white; border: none; padding: 13px 18px; }
QPushButton#primary:hover { background: #4354c4; }
QPushButton:disabled { color: #8793a8; background: #e9edf5; border-color: #e9edf5; }
QPushButton#primary:disabled { background: #c6cee9; color: #ffffff; }
QPushButton#quiet { background: transparent; color: #65748b; border: none; }
QFrame#dropZone { background: #f7f8ff; border: 2px dashed #c2cbee; border-radius: 14px; }
QFrame#dropZone[dragActive="true"] { background: #e7edff; border-color: #5365d9; }
QFrame#dropZone:disabled { background: #f0f2f6; border-color: #d8dfe9; }
QLabel#dropIcon { font-size: 28px; font-weight: 600; color: #5365d9; }
QLabel#preview { background: #f1f4f9; border: 1px solid #e4e9f2; border-radius: 12px; color: #8390a3; }
QLineEdit, QComboBox { background: #f8f9fc; border: 1px solid #dbe1ed; border-radius: 8px; padding: 10px; selection-background-color: #5365d9; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #e7edff; selection-color: #243249; }
QTableWidget { background: white; border: none; gridline-color: #edf0f6; selection-background-color: #edf1ff; selection-color: #243249; }
QHeaderView::section { background: #f8f9fc; border: none; padding: 10px; color: #718097; font-size: 11px; font-weight: 700; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid #eef1f7; }
QProgressBar { background: #e7ebf5; border: none; border-radius: 4px; min-height: 7px; max-height: 7px; }
QProgressBar::chunk { background: #5365d9; border-radius: 4px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #f3f5fa; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #c8d1e2; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #243249; color: white; border: none; padding: 8px; }
'''
