"""Qt integration: real events and worker, synthetic images and mocked OS dialogs."""
import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication

pytestmark = pytest.mark.ui


def drop(widget, urls):
    mime = QMimeData()
    mime.setUrls(urls)
    # QPoint is needed for supported Qt 6.8-6.11; Qt 6.12 deprecates this overload.
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Function:.*QDragEnterEvent.*', category=DeprecationWarning)
        enter = QDragEnterEvent(QPoint(20, 20), Qt.DropAction.CopyAction, mime,
                               Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(widget, enter)
    event = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(widget, event)
    return enter.isAccepted(), event.isAccepted()


def test_local_drop_and_duplicate(window, image_factory):
    source = image_factory()
    urls = [QUrl.fromLocalFile(str(source))]
    assert drop(window.view.drop_zone, urls) == (True, True)
    assert window.paths == [source]
    drop(window.view.drop_zone, urls)
    assert window.view.table.rowCount() == 1
    assert not window.view.preview.pixmap().isNull()
    assert window.view.start.isEnabled()


def test_folder_drop(window, tmp_path, image_factory):
    source = image_factory()
    assert drop(window.view.drop_zone, [QUrl.fromLocalFile(str(tmp_path))]) == (True, True)
    assert window.paths == [source]


def test_remote_drop_rejected(window):
    assert drop(window.view.drop_zone, [QUrl('https://example.com/photo.png')]) == (False, False)
    assert window.paths == []


def test_output_picker_and_batch(window, qtbot, tmp_path, image_factory, monkeypatch, preferences):
    source = image_factory()
    window.add_paths([str(source)])
    destination = tmp_path / 'minhas imagens limpas'
    destination.mkdir()
    monkeypatch.setattr('pixel_livre.ui.window.QFileDialog.getExistingDirectory', lambda *args: str(destination))
    qtbot.mouseClick(window.view.choose_folder, Qt.MouseButton.LeftButton)
    assert preferences.destination == str(destination)
    qtbot.mouseClick(window.view.start, Qt.MouseButton.LeftButton)
    assert not window.view.drop_zone.isEnabled()
    assert not window.view.destination.isEnabled()
    qtbot.waitUntil(lambda: not window.busy, timeout=10000)
    assert (destination / 'foto com ação_limpa.png').exists()
    assert '1 salva(s)' in window.view.status.text()
    assert window.view.drop_zone.isEnabled()


def test_remove_and_cancelled_folder_dialog(window, image_factory, monkeypatch):
    window.add_paths([str(image_factory())])
    before = window.view.destination.text()
    monkeypatch.setattr('pixel_livre.ui.window.QFileDialog.getExistingDirectory', lambda *args: '')
    window.select_output_folder()
    assert window.view.destination.text() == before
    window.remove_selected()
    assert not window.paths
    assert not window.view.start.isEnabled()


def test_minimum_layout_keeps_primary_action_visible(window, qtbot, image_factory):
    window.resize(940, 720)
    qtbot.waitUntil(lambda: window.width() == 940)
    button = window.view.start
    bottom = button.mapTo(window, button.rect().bottomRight())
    assert bottom.y() < window.height()
    assert bottom.x() < window.width()
    window.add_paths([str(image_factory())])
    assert not window.view.empty.isVisible()


def test_invalid_destination_keeps_app_idle(window, image_factory, monkeypatch):
    source = image_factory()
    window.add_paths([str(source)])
    window.view.destination.setText(str(source))
    messages = []
    monkeypatch.setattr('pixel_livre.ui.window.QMessageBox.warning', lambda *args: messages.append(args[2]))
    window.start_batch()
    assert not window.busy
    assert window.worker is None
    assert 'arquivo' in messages[0]


def test_blank_destination_disables_start(window, image_factory):
    window.add_paths([str(image_factory())])
    window.view.destination.setText('  ')
    assert not window.view.start.isEnabled()


def test_bad_image_shows_failure_and_recovers_controls(window, qtbot, tmp_path):
    source = tmp_path / 'broken.png'
    source.write_bytes(b'broken')
    window.add_paths([str(source)])
    assert window.view.preview.text() == 'Prévia indisponível'
    window.start_batch()
    qtbot.waitUntil(lambda: not window.busy, timeout=10000)
    assert '1 erro(s)' in window.view.status.text()
    assert window.view.table.item(0, 1).text().startswith('Erro:')
    assert window.view.start.isEnabled()
