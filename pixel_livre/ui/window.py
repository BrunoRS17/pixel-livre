"""Window controller: connect user actions, preferences and the batch worker."""
from pathlib import Path
import warnings

from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QColor, QDesktopServices, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTableWidgetItem

from pixel_livre.core.batch import BatchSummary, ImageResult
from pixel_livre.core.importing import collect_images
from pixel_livre.settings import Preferences
from .view import WindowView
from .worker import CleaningWorker
from .privacy import PrivacyDialog


class MainWindow(QMainWindow):
    """Own UI state. Worker signals are delivered on the GUI thread."""
    def __init__(self, preferences: Preferences):
        super().__init__()
        self.preferences = preferences
        self.paths: list[Path] = []
        self.worker: CleaningWorker | None = None
        self.busy = False
        self.setWindowTitle('Pixel Livre • Suas imagens, sem metadados')
        self.resize(1120, 850)
        self.setMinimumSize(940, 720)
        self.view = WindowView()
        self.setCentralWidget(self.view)
        v = self.view
        v.destination.setText(preferences.destination)
        v.output_format.setCurrentIndex(v.output_format.findData(preferences.output_format))
        v.drop_zone.files_dropped.connect(self.add_paths)
        v.add_files.clicked.connect(self.select_files)
        v.add_folder.clicked.connect(self.select_input_folder)
        v.remove.clicked.connect(self.remove_selected)
        v.choose_folder.clicked.connect(self.select_output_folder)
        v.start.clicked.connect(self.start_batch)
        v.cancel.clicked.connect(self.cancel_batch)
        v.open_folder.clicked.connect(self.open_output_folder)
        v.privacy.clicked.connect(self.show_privacy)
        v.table.itemSelectionChanged.connect(self.show_preview)
        v.destination.textChanged.connect(self.refresh)
        v.output_format.currentIndexChanged.connect(self.update_format_hint)
        self.delete_shortcut = QShortcut(QKeySequence('Delete'), v.table)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.remove_selected)
        self.update_format_hint()
        self.refresh()

    @Slot()
    def select_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, 'Escolha suas imagens', '',
            'Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)')
        self.add_paths(paths)

    @Slot()
    def select_input_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, 'Pasta com imagens')
        if folder:
            self.add_paths([folder])

    @Slot(list)
    def add_paths(self, inputs: list[str]) -> None:
        if self.busy or not inputs:
            return
        result = collect_images(inputs, self.paths)
        v = self.view
        for path in result.paths:
            row = v.table.rowCount()
            v.table.insertRow(row)
            item = QTableWidgetItem(path.name)
            item.setToolTip(str(path))
            v.table.setItem(row, 0, item)
            v.table.setItem(row, 1, QTableWidgetItem('Aguardando'))
            self.paths.append(path)
        if self.paths and not v.destination.text().strip():
            v.destination.setText(str(self.paths[0].parent / 'Imagens limpas'))
        if result.paths:
            v.table.selectRow(v.table.rowCount() - len(result.paths))
        message = f'{len(result.paths)} adicionada(s)'
        if result.ignored:
            message += f' · {result.ignored} ignorada(s): duplicadas, subpastas ou incompatíveis'
        if not result.paths:
            message += '. Use PNG, JPEG, WebP, BMP ou TIFF.'
        if result.errors:
            message += ' · Não foi possível ler alguns caminhos.'
        v.import_status.setText(message)
        v.import_status.setToolTip('\n'.join(result.errors))
        self.refresh()

    @Slot()
    def remove_selected(self) -> None:
        if self.busy:
            return
        rows = sorted({item.row() for item in self.view.table.selectedIndexes()}, reverse=True)
        self.view.table.blockSignals(True)
        for row in rows:
            self.paths.pop(row)
            self.view.table.removeRow(row)
        self.view.table.blockSignals(False)
        self.show_preview()
        self.refresh()

    @Slot()
    def show_preview(self) -> None:
        v = self.view
        v.preview.clear()
        v.preview.setText('Prévia da imagem')
        v.details.setText('Selecione um arquivo na lista.')
        self.refresh()
        selected = v.table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        path = self.paths[row]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(path) as source:
                    # Request decoder downsampling before orientation on large JPEGs.
                    size = source.size
                    source.draft('RGB', (640, 400))
                    thumb = ImageOps.exif_transpose(source)
                    thumb.thumbnail((310, 150))
                    rgba = thumb.convert('RGBA')
                    data = rgba.tobytes()
                    image = QImage(data, rgba.width, rgba.height, rgba.width * 4,
                                   QImage.Format.Format_RGBA8888).copy()
                    v.preview.setPixmap(QPixmap.fromImage(image))
            status = v.table.item(row, 1).text()
            v.details.setText(f'{path.name}\n{size[0]} × {size[1]} px · {path.stat().st_size / 1024:.0f} KB\n{status}')
        except Exception as error:
            v.preview.setText('Prévia indisponível')
            v.details.setText(f'{path.name}\n{error}')

    @Slot()
    def select_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, 'Onde salvar as cópias limpas?', self.view.destination.text())
        if folder:
            self.view.destination.setText(folder)
            self.preferences.save(folder, self.view.output_format.currentData())

    @Slot()
    def update_format_hint(self) -> None:
        hints = {
            'PNG': 'Preserva transparência. Pode gerar arquivos maiores.',
            'JPEG': 'Qualidade 95. Recompressão com transparência em branco.',
            'WEBP': 'Compressão sem perdas, com transparência.',
        }
        self.view.format_hint.setText(hints[self.view.output_format.currentData()] +
            '\nPerfis de cor são removidos; as cores podem variar.')

    @Slot()
    def show_privacy(self) -> None:
        selected = self.view.table.selectionModel().selectedRows()
        if self.busy or len(selected) != 1:
            return
        self.privacy_dialog = PrivacyDialog(self.paths[selected[0].row()], self)
        self.privacy_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.privacy_dialog.open()

    @Slot()
    def refresh(self) -> None:
        v = self.view
        v.count.setText(f'Sua seleção · {len(self.paths)}')
        v.empty.setVisible(not self.paths)
        v.start.setEnabled(bool(self.paths) and bool(v.destination.text().strip()) and not self.busy)
        v.remove.setEnabled(bool(v.table.selectedIndexes()) and not self.busy)
        v.privacy.setEnabled(len(v.table.selectionModel().selectedRows()) == 1 and not self.busy)
        v.destination.setToolTip(v.destination.text())

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        v = self.view
        for control in (v.add_files, v.add_folder, v.drop_zone, v.choose_folder, v.destination, v.output_format):
            control.setEnabled(not busy)
        v.cancel.setVisible(busy)
        v.cancel.setEnabled(busy)
        self.refresh()

    @Slot()
    def start_batch(self) -> None:
        v = self.view
        if self.busy or not self.paths or not v.destination.text().strip():
            return
        try:
            destination = Path(v.destination.text().strip()).expanduser().resolve()
            if destination.exists() and not destination.is_dir():
                raise ValueError('O destino é um arquivo. Escolha uma pasta.')
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, 'Pasta inválida', str(error))
            return
        v.destination.setText(str(destination))
        self.preferences.save(str(destination), v.output_format.currentData())
        for row in range(len(self.paths)):
            self.set_result(row, 'Aguardando', '#718097')
        v.progress.setRange(0, len(self.paths))
        v.progress.setValue(0)
        v.status.setText('Preparando suas imagens…')
        self.set_busy(True)
        self.worker = CleaningWorker(self.paths, destination, v.output_format.currentData(), self)
        self.worker.image_started.connect(self.image_started)
        self.worker.image_finished.connect(self.image_finished)
        self.worker.batch_finished.connect(self.batch_finished)
        self.worker.finished.connect(self.worker_stopped)
        self.worker.start()

    def set_result(self, row: int, text: str, color: str) -> None:
        item = self.view.table.item(row, 1)
        item.setText(text)
        item.setForeground(QColor(color))
        item.setToolTip(text)

    @Slot(int)
    def image_started(self, row: int) -> None:
        self.set_result(row, 'Limpando…', '#5365d9')
        self.view.status.setText(f'Limpando {row + 1} de {len(self.paths)}…')

    @Slot(object)
    def image_finished(self, result: ImageResult) -> None:
        if result.error is not None:
            self.set_result(result.index, f'Erro: {result.error}', '#b53c4b')
        else:
            self.set_result(result.index, f'Salva: {result.output.name}', '#18765e')
        self.view.progress.setValue(self.view.progress.value() + 1)

    @Slot(object)
    def batch_finished(self, summary: BatchSummary) -> None:
        self.view.status.setText(f'{summary.saved} salva(s) · {summary.failed} erro(s) · {summary.skipped} não processada(s)')
        for row in range(summary.saved + summary.failed, len(self.paths)):
            self.set_result(row, 'Não processada', '#718097')
        self.show_preview()

    @Slot()
    def worker_stopped(self) -> None:
        # Enable controls only after QThread has really stopped (safe to close).
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()
        self.set_busy(False)

    @Slot()
    def cancel_batch(self) -> None:
        if self.worker:
            self.worker.cancel_requested.set()
            self.view.cancel.setEnabled(False)
            self.view.status.setText('Cancelando após a imagem atual…')

    @Slot()
    def open_output_folder(self) -> None:
        text = self.view.destination.text().strip()
        folder = Path(text).expanduser() if text else None
        if folder and folder.is_dir():
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve()))):
                QMessageBox.warning(self, 'Pasta de saída', 'Não foi possível abrir esta pasta.')
        else:
            QMessageBox.information(self, 'Pasta de saída', 'Escolha uma pasta. Ela será criada ao salvar a primeira imagem.')

    def closeEvent(self, event) -> None:
        if self.busy:
            QMessageBox.information(self, 'Limpeza em andamento', 'Cancele ou aguarde a limpeza antes de fechar.')
            event.ignore()
        else:
            self.preferences.save(self.view.destination.text().strip(), self.view.output_format.currentData())
            event.accept()
