"""Composition root: instantiate dependencies and start Qt."""
import sys
from PySide6.QtWidgets import QApplication
from .settings import Preferences
from .ui.theme import STYLESHEET
from .ui.window import MainWindow


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test-dir':
        from .diagnostics import run_self_test
        return run_self_test(sys.argv[2])
    application = QApplication(sys.argv)
    application.setApplicationName('Pixel Livre')
    application.setStyle('Fusion')
    application.setStyleSheet(STYLESHEET)
    window = MainWindow(Preferences())
    window.show()
    return application.exec()
