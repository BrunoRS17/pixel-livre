"""Preferences round-trip through an isolated INI file, not the user registry."""
import pytest
from PySide6.QtCore import QSettings
from pixel_livre.settings import Preferences


def test_defaults(preferences):
    assert preferences.destination == ''
    assert preferences.output_format == 'PNG'


@pytest.mark.parametrize('output_format', ['PNG', 'JPEG', 'WEBP'])
def test_persistence(tmp_path, preferences, output_format):
    destination = str(tmp_path / 'imagens com acentuação')
    preferences.save(destination, output_format)
    reloaded = Preferences(QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat))
    assert reloaded.destination == destination
    assert reloaded.output_format == output_format


def test_invalid_saved_format_falls_back_to_png(preferences):
    preferences.storage.setValue('export/format', 'INVALID')
    assert preferences.output_format == 'PNG'
