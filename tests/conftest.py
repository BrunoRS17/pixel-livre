"""Shared pytest fixtures: synthetic images, isolated preferences and Qt cleanup."""
import os

# Set before QApplication is created; developers can override this for visible tests.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PIL import Image
from PySide6.QtCore import QSettings
from pixel_livre.settings import Preferences
from pixel_livre.ui.theme import STYLESHEET
from pixel_livre.ui.window import MainWindow


@pytest.fixture
def image_factory(tmp_path):
    """Create real, tiny images without using private photos or network access."""
    def create(name='foto com ação.png', mode='RGBA', color=(20, 60, 120, 128), **save_options):
        path = tmp_path / name
        Image.new(mode, (40, 20), color).save(path, **save_options)
        return path
    return create


@pytest.fixture
def preferences(tmp_path):
    return Preferences(QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat))


@pytest.fixture
def window(qtbot, qapp, preferences):
    """Always stop processing before Qt destroys a window, even after assertion failure."""
    qapp.setStyle('Fusion')
    qapp.setStyleSheet(STYLESHEET)
    widget = MainWindow(preferences)
    qtbot.addWidget(widget)
    widget.show()
    yield widget
    if widget.worker is not None:
        widget.worker.cancel_requested.set()
        qtbot.waitUntil(lambda: not widget.busy, timeout=10000)
    widget.close()
