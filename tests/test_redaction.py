"""Verify irreversible pixel replacement, coordinate mapping and export workflow."""
import pytest
from PIL import Image
from PySide6.QtCore import Qt, QPointF
from pixel_livre.core.redaction import load_pixels, export_redacted


def test_redaction_flattens_alpha_preserves_outside_and_original(tmp_path):
    path = tmp_path / 'original.png'
    exif = Image.Exif()
    exif[315] = 'Private author'
    Image.new('RGBA', (40, 30), (20, 90, 150, 80)).save(path, exif=exif)
    original = path.read_bytes()
    image = load_pixels(path)
    result = export_redacted(image, ((2, 3, 12, 13), (8, 8, 20, 20)), tmp_path, path.stem)
    with Image.open(result) as saved:
        assert saved.size == image.size
        assert not saved.getexif()
        assert not saved.info
        for y in range(30):
            for x in range(40):
                covered = (2 <= x < 12 and 3 <= y < 13) or (8 <= x < 20 and 8 <= y < 20)
                assert saved.getpixel((x, y)) == ((0, 0, 0, 255) if covered else (20, 90, 150, 80))
    assert path.read_bytes() == original
    assert image.getpixel((5, 5)) == (20, 90, 150, 80)
    again = export_redacted(image, ((0, 0, 40, 30),), tmp_path, path.stem)
    assert again != result
    with Image.open(again) as saved:
        assert saved.getextrema() == ((0, 0), (0, 0), (0, 0), (255, 255))


def test_orientation_and_snapshot(tmp_path):
    path = tmp_path / 'rotated.png'
    exif = Image.Exif()
    exif[274] = 6
    Image.new('RGB', (40, 20), 'white').save(path, exif=exif)
    image = load_pixels(path)
    assert image.size == (20, 40)
    path.write_bytes(b'changed after opening')
    target = export_redacted(image, ((0, 0, 10, 10),), tmp_path, 'snapshot')
    with Image.open(target) as saved:
        assert saved.size == (20, 40)
        assert saved.getpixel((15, 35)) == (255, 255, 255, 255)


@pytest.mark.parametrize('regions', [(), ((0, 0, 0, 1),), ((-1, 0, 5, 5),), ((0, 0, 11, 5),), ((0.1, 0, 5, 5),), ((1, 2, 3),)])
def test_invalid_regions_never_write(tmp_path, regions):
    destination = tmp_path / 'out'
    with pytest.raises(ValueError):
        export_redacted(Image.new('RGBA', (10, 10)), regions, destination, 'test')
    assert not destination.exists()


def test_bad_or_multiframe_input(tmp_path):
    path = tmp_path / 'bad.png'
    path.write_bytes(b'invalid')
    with pytest.raises(OSError):
        load_pixels(path)
    image = Image.new('RGB', (10, 10))
    path = tmp_path / 'pages.tiff'
    image.save(path, save_all=True, append_images=[image])
    with pytest.raises(ValueError, match='páginas'):
        load_pixels(path)


def drag(qtbot, canvas, start, end):
    first = canvas.mapFromScene(QPointF(*start))
    last = canvas.mapFromScene(QPointF(*end))
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=first)
    qtbot.mouseMove(canvas.viewport(), last)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=last)


@pytest.mark.ui
def test_editor_export_zoom_undo_and_clear(window, qtbot, image_factory, tmp_path, monkeypatch):
    assert not window.view.redact.isEnabled()
    window.add_paths([str(image_factory())])
    qtbot.mouseClick(window.view.redact, Qt.MouseButton.LeftButton)
    editor = window.redaction_dialog
    qtbot.waitUntil(lambda: not editor.working)
    assert not editor.save.isEnabled()
    drag(qtbot, editor.canvas, (4, 4), (20, 15))
    assert len(editor.canvas.regions) == 1
    qtbot.mouseClick(editor.plus, Qt.MouseButton.LeftButton)
    drag(qtbot, editor.canvas, (28, 16), (22, 10))
    assert len(editor.canvas.regions) == 2
    qtbot.mouseClick(editor.undo_button, Qt.MouseButton.LeftButton)
    assert len(editor.canvas.regions) == 1
    monkeypatch.setattr('pixel_livre.ui.redaction.QFileDialog.getExistingDirectory', lambda *args: str(tmp_path))
    qtbot.mouseClick(editor.save, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: not editor.working)
    assert editor.output.is_file()
    with Image.open(editor.output) as saved:
        assert saved.getpixel((10, 10)) == (0, 0, 0, 255)
        assert saved.getpixel((35, 18)) == (20, 60, 120, 128)
    qtbot.mouseClick(editor.clear_button, Qt.MouseButton.LeftButton)
    assert not editor.canvas.regions
    assert not editor.save.isEnabled()
    editor.close()


@pytest.mark.ui
def test_editor_load_failure_and_cancel_save(window, qtbot, image_factory, tmp_path, monkeypatch):
    path = tmp_path / 'bad.png'
    path.write_bytes(b'bad')
    window.add_paths([str(path)])
    window.show_redaction()
    editor = window.redaction_dialog
    qtbot.waitUntil(lambda: not editor.working)
    assert 'Não foi possível' in editor.status.text()
    assert not editor.save.isEnabled()
    editor.close()
    window.remove_selected()
    window.add_paths([str(image_factory())])
    window.show_redaction()
    editor = window.redaction_dialog
    qtbot.waitUntil(lambda: not editor.working)
    drag(qtbot, editor.canvas, (3, 3), (15, 15))
    monkeypatch.setattr('pixel_livre.ui.redaction.QFileDialog.getExistingDirectory', lambda *args: '')
    editor.save_copy()
    assert editor.output is None
    assert not editor.working
    editor.close()


@pytest.mark.ui
def test_canvas_clips_reverse_drag_and_ignores_click(qtbot):
    from pixel_livre.ui.redaction import RedactionCanvas
    canvas = RedactionCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(600, 400)
    canvas.show()
    canvas.set_image(Image.new('RGBA', (100, 50)))
    drag(qtbot, canvas, (20, 20), (20, 20))
    assert not canvas.regions
    drag(qtbot, canvas, (60, 30), (-10, -10))
    box = canvas.regions[0]
    assert box[:2] == (0, 0)
    assert 59 <= box[2] <= 61
    assert 29 <= box[3] <= 31
    canvas.clear_regions()
    canvas.zoom(1.25)
    drag(qtbot, canvas, (10, 10), (30, 30))
    left, top, right, bottom = canvas.regions[0]
    assert 9 <= left <= 11 and 9 <= top <= 11
    assert 29 <= right <= 31 and 29 <= bottom <= 31


@pytest.mark.ui
def test_editor_busy_close_and_export_failure(window, qtbot, image_factory, tmp_path, monkeypatch):
    from threading import Event
    from pixel_livre.core.redaction import load_pixels as real_load
    gate = Event()
    source = image_factory()

    def delayed(path):
        gate.wait(5)
        return real_load(path)

    monkeypatch.setattr('pixel_livre.ui.redaction.load_pixels', delayed)
    window.add_paths([str(source)])
    window.show_redaction()
    editor = window.redaction_dialog
    try:
        editor.reject()
        editor.close()
        assert editor.isVisible()
        assert not editor.close_button.isEnabled()
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not editor.working)
    drag(qtbot, editor.canvas, (2, 2), (20, 15))
    monkeypatch.setattr('pixel_livre.ui.redaction.QFileDialog.getExistingDirectory', lambda *args: str(source))
    editor.save_copy()
    qtbot.waitUntil(lambda: not editor.working)
    assert editor.output is None
    assert 'Não foi possível' in editor.status.text()
    assert editor.save.isEnabled()
    editor.close()
