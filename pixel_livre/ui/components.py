"""Reusable presentation components and local-file drop handling."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


def label(text: str, role: str = '', wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setObjectName(role)
    widget.setWordWrap(wrap)
    return widget


class DropZone(QFrame):
    """Accept local file URLs; Qt decoding preserves spaces and Unicode."""
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName('dropZone')
        self.setMinimumHeight(128)
        self.setAcceptDrops(True)
        self.setAccessibleName('Área para arrastar imagens e pastas')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(5)
        for text, role in [('↓', 'dropIcon'), ('Arraste suas imagens para cá', 'section'),
                           ('Ou selecione arquivos e pastas pelos botões abaixo.', 'muted')]:
            item = label(text, role, True)
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setMinimumHeight(item.sizeHint().height())
            layout.addWidget(item)

    def _highlight(self, active: bool) -> None:
        self.setProperty('dragActive', active)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event) -> None:
        if self.isEnabled() and any(url.isLocalFile() for url in event.mimeData().urls()):
            self._highlight(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dragLeaveEvent(self, event) -> None:
        self._highlight(False)
        event.accept()

    def dropEvent(self, event) -> None:
        self._highlight(False)
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if self.isEnabled() and paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
        else:
            event.ignore()
