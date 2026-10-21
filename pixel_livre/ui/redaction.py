"""Rectangle editor with source-coordinate selections and background I/O."""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QRectF
from PySide6.QtGui import QImage, QPixmap, QPen, QBrush
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsView, QGraphicsScene, QFileDialog)
from pixel_livre.core.redaction import load_pixels, export_redacted


class ImageTask(QThread):
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, operation, parent):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            self.result.emit(self.operation())
        except Exception as error:
            self.failed.emit(str(error))


class RedactionCanvas(QGraphicsView):
    """Map viewport drags to bounded source pixels, independent of zoom/scroll."""
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('redactionCanvas')
        self.setAccessibleName('Imagem: arraste para cobrir regiões com preto')
        self.setScene(QGraphicsScene(self))
        self.regions = []
        self.masks = []
        self.origin = None
        self.rubber = None
        self.bounds = QRectF()
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_image(self, image):
        data = image.tobytes()
        qimage = QImage(data, image.width, image.height, image.width * 4, QImage.Format.Format_RGBA8888).copy()
        self.scene().addPixmap(QPixmap.fromImage(qimage))
        self.bounds = QRectF(0, 0, image.width, image.height)
        self.setSceneRect(self.bounds)
        self.fit_image()

    def fit_image(self):
        self.fitInView(self.bounds, Qt.AspectRatioMode.KeepAspectRatio)

    def zoom(self, factor):
        if 0.02 <= self.transform().m11() * factor <= 32:
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.bounds.isEmpty():
            point = self.mapToScene(event.position().toPoint())
            if self.bounds.contains(point):
                self.origin = point
                self.rubber = self.scene().addRect(QRectF(point, point), QPen(Qt.GlobalColor.black, 0), QBrush(Qt.GlobalColor.black))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            box = QRectF(self.origin, self.mapToScene(event.position().toPoint())).normalized().intersected(self.bounds)
            self.rubber.setRect(box)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.origin is not None:
            box = QRectF(self.origin, self.mapToScene(event.position().toPoint())).normalized().intersected(self.bounds)
            if box.width() >= 1 and box.height() >= 1:
                region = (math.floor(box.left()), math.floor(box.top()), math.ceil(box.right()), math.ceil(box.bottom()))
                self.regions.append(region)
                self.rubber.setRect(QRectF(region[0], region[1], region[2]-region[0], region[3]-region[1]))
                self.masks.append(self.rubber)
            else:
                self.scene().removeItem(self.rubber)
            self.origin = self.rubber = None
            self.changed.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def undo(self):
        if self.regions:
            self.regions.pop()
            self.scene().removeItem(self.masks.pop())
            self.changed.emit()

    def clear_regions(self):
        while self.regions:
            self.undo()


class RedactionDialog(QDialog):
    """Export only the frozen preview snapshot; never reopen an edited source."""
    def __init__(self, path: Path, destination: str, parent=None):
        super().__init__(parent)
        self.setObjectName('redactionDialog')
        self.setWindowTitle('Ocultar informações • Pixel Livre')
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(960, 720)
        self.setMinimumSize(640, 500)
        self.path, self.destination = path, destination
        self.image = None
        self.task = None
        self.working = False
        self.output = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel('Ocultar informações')
        title.setObjectName('title')
        layout.addWidget(title)
        hint = QLabel('Arraste sobre a imagem para cobrir uma região. Use o zoom para ajustar a seleção.\nAs áreas marcadas serão substituídas por preto opaco na cópia PNG, sem metadados.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        toolbar = QHBoxLayout()
        self.minus, self.plus, self.fit = QPushButton('− Zoom'), QPushButton('+ Zoom'), QPushButton('Ajustar')
        self.undo_button, self.clear_button = QPushButton('Desfazer'), QPushButton('Limpar marcações')
        for button in (self.minus, self.plus, self.fit, self.undo_button, self.clear_button):
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.canvas = RedactionCanvas()
        layout.addWidget(self.canvas, 1)
        self.status = QLabel('Carregando imagem…')
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        note = QLabel('O original será preservado.\nConfira todas as regiões antes de compartilhar a cópia.')
        note.setObjectName('muted')
        footer.addWidget(note, 1)
        self.close_button, self.save = QPushButton('Fechar'), QPushButton('Salvar cópia protegida')
        self.save.setObjectName('primary')
        footer.addWidget(self.close_button)
        footer.addWidget(self.save)
        layout.addLayout(footer)
        self.minus.clicked.connect(lambda: self.canvas.zoom(0.8))
        self.plus.clicked.connect(lambda: self.canvas.zoom(1.25))
        self.fit.clicked.connect(self.canvas.fit_image)
        self.undo_button.clicked.connect(self.canvas.undo)
        self.clear_button.clicked.connect(self.canvas.clear_regions)
        self.canvas.changed.connect(self.selection_changed)
        self.close_button.clicked.connect(self.reject)
        self.save.clicked.connect(self.save_copy)
        self.run_task(lambda: load_pixels(path), self.loaded)

    def refresh(self):
        ready = self.image is not None and not self.working
        for control in (self.canvas, self.minus, self.plus, self.fit):
            control.setEnabled(ready)
        for control in (self.undo_button, self.clear_button, self.save):
            control.setEnabled(ready and bool(self.canvas.regions))
        self.close_button.setEnabled(not self.working)

    def run_task(self, operation, callback):
        self.working = True
        self.refresh()
        self.task = ImageTask(operation, self)
        self.task.result.connect(callback)
        self.task.failed.connect(lambda message: self.status.setText('Não foi possível concluir: ' + message))
        self.task.finished.connect(self.task_finished)
        self.task.start()

    def task_finished(self):
        self.working = False
        self.task.deleteLater()
        self.task = None
        self.refresh()

    def loaded(self, image):
        self.image = image
        self.canvas.set_image(image)
        self.selection_changed()

    def selection_changed(self):
        self.status.setText(f'{len(self.canvas.regions)} região(ões) marcada(s) · exportação em PNG')
        self.refresh()

    def save_copy(self):
        if self.working or not self.canvas.regions:
            return
        folder = QFileDialog.getExistingDirectory(self, 'Onde salvar a cópia protegida?', self.destination)
        if not folder:
            return
        self.export_to(folder)

    def export_to(self, folder):
        """Start export to an explicit folder; shared by picker and diagnostics."""
        if self.working or not self.canvas.regions:
            return
        self.destination = folder
        regions = tuple(self.canvas.regions)
        self.status.setText('Salvando cópia protegida…')
        self.run_task(lambda: export_redacted(self.image, regions, Path(folder), self.path.stem), self.saved)

    def saved(self, path):
        self.output = path
        self.status.setText(f'Cópia salva: {path}')

    def reject(self):
        if not self.working:
            super().reject()

    def closeEvent(self, event):
        if self.working:
            event.ignore()
        else:
            super().closeEvent(event)
