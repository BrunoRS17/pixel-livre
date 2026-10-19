"""Qt adapter for batch processing; widgets stay on the main thread."""
from pathlib import Path
from threading import Event
from PySide6.QtCore import QThread, Signal
from pixel_livre.core.batch import run_batch


class CleaningWorker(QThread):
    image_started = Signal(int)
    image_finished = Signal(object)
    batch_finished = Signal(object)

    def __init__(self, paths: list[Path], destination: Path, output_format: str, parent=None):
        super().__init__(parent)
        self.paths = tuple(paths)
        self.destination = destination
        self.output_format = output_format
        self.cancel_requested = Event()

    def run(self) -> None:
        summary = run_batch(
            self.paths, self.destination, self.output_format, self.cancel_requested,
            self.image_started.emit, self.image_finished.emit,
        )
        self.batch_finished.emit(summary)
