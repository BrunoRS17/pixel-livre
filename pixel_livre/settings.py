"""Persist export preferences only, never image contents or history."""
from PySide6.QtCore import QSettings


class Preferences:
    """Inject QSettings in tests to avoid changing user settings."""
    def __init__(self, storage: QSettings | None = None):
        self.storage = storage if storage is not None else QSettings('PixelLivre', 'PixelLivre')

    @property
    def destination(self) -> str:
        return str(self.storage.value('export/destination', ''))

    @property
    def output_format(self) -> str:
        value = str(self.storage.value('export/format', 'PNG'))
        return value if value in {'PNG', 'JPEG', 'WEBP'} else 'PNG'

    def save(self, destination: str, output_format: str) -> None:
        self.storage.setValue('export/destination', destination)
        self.storage.setValue('export/format', output_format)
        self.storage.sync()
