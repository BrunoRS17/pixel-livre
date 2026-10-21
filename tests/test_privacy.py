"""Synthetic privacy evidence and real asynchronous UI integration."""
import pytest
from PIL import Image, PngImagePlugin
from PySide6.QtCore import Qt
from pixel_livre.core.cleaning import clean_image
from pixel_livre.core.privacy import inspect_privacy, readable


def tagged_image(tmp_path):
    path = tmp_path / 'privacidade.png'
    exif = Image.Exif()
    exif[315] = 'Autora de teste'
    exif[271] = 'Câmera de teste'
    exif[34665] = {36867: '2026:01:02 12:30:00', 42033: 'SERIAL-TESTE'}
    exif[34853] = {1: 'S', 2: (23.0, 30.0, 0.0), 3: 'W', 4: (46.0, 30.0, 0.0)}
    text = PngImagePlugin.PngInfo()
    text.add_text('Comment', '<b>conteúdo literal</b>')
    text.add_itxt('XML:com.adobe.xmp', '<xmp>teste</xmp>')
    Image.new('RGB', (10, 10)).save(path, exif=exif, pnginfo=text)
    return path


def test_sensitive_metadata_and_original_preserved(tmp_path):
    path = tagged_image(tmp_path)
    original = path.read_bytes()
    report = inspect_privacy(path)
    assert not report.warnings
    assert {'Identificação', 'Localização', 'Data e horário', 'Dispositivo e software'} <= {f.category for f in report.findings}
    assert any(f.value == 'SERIAL-TESTE' for f in report.findings)
    assert any(f.field == 'XML:com.adobe.xmp' for f in report.findings)
    assert path.read_bytes() == original


@pytest.mark.parametrize('output_format', ['PNG', 'JPEG', 'WEBP'])
def test_cleaned_image_has_no_detected_metadata(tmp_path, output_format):
    original = tagged_image(tmp_path)
    clean = clean_image(original, tmp_path / 'out', output_format)
    assert not inspect_privacy(clean).findings


def test_unreadable_is_not_reported_as_clean(tmp_path):
    path = tmp_path / 'broken.jpg'
    path.write_bytes(b'broken')
    with pytest.raises(OSError):
        inspect_privacy(path)


def test_malformed_exif_reports_incomplete(tmp_path, monkeypatch):
    path = tagged_image(tmp_path)
    monkeypatch.setattr(Image.Exif, 'get_ifd', lambda *args: (_ for _ in ()).throw(ValueError('bad EXIF')))
    assert inspect_privacy(path).warnings


def test_binary_profile_and_bounded_values(tmp_path):
    path = tmp_path / 'profile.png'
    Image.new('RGB', (10, 10)).save(path, icc_profile=b'fake-profile')
    report = inspect_privacy(path)
    assert report.findings[0].field == 'icc_profile'
    assert '12 bytes' in report.findings[0].value
    assert len(readable('x' * 1000)) == 501
    assert readable('a\nb') == 'a b'


def test_multiframe_warning(tmp_path):
    path = tmp_path / 'pages.tiff'
    image = Image.new('RGB', (10, 10))
    image.save(path, save_all=True, append_images=[image])
    assert inspect_privacy(path).warnings


@pytest.mark.ui
def test_privacy_dialog_and_selection(window, qtbot, tmp_path):
    assert not window.view.privacy.isEnabled()
    path = tagged_image(tmp_path)
    window.add_paths([str(path)])
    qtbot.mouseClick(window.view.privacy, Qt.MouseButton.LeftButton)
    dialog = window.privacy_dialog
    qtbot.waitUntil(lambda: dialog.close_button.isEnabled(), timeout=10000)
    assert 'Autora de teste' in dialog.details.toPlainText()
    assert '<b>conteúdo literal</b>' in dialog.details.toPlainText()
    assert 'campo(s)' in dialog.heading.text()
    dialog.reject()
    window.remove_selected()
    assert not window.view.privacy.isEnabled()


@pytest.mark.ui
def test_privacy_dialog_failure(window, qtbot, tmp_path):
    path = tmp_path / 'broken.png'
    path.write_bytes(b'invalid')
    window.add_paths([str(path)])
    window.show_privacy()
    dialog = window.privacy_dialog
    qtbot.waitUntil(lambda: dialog.close_button.isEnabled(), timeout=10000)
    assert 'Não foi possível analisar' in dialog.heading.text()
    dialog.close()


@pytest.mark.ui
def test_busy_dialog_cannot_close_and_empty_report(window, qtbot, image_factory, monkeypatch):
    from threading import Event
    from pixel_livre.core.privacy import PrivacyReport
    gate = Event()

    def delayed(path):
        gate.wait(5)
        return PrivacyReport(())

    monkeypatch.setattr('pixel_livre.ui.privacy.inspect_privacy', delayed)
    window.add_paths([str(image_factory())])
    window.show_privacy()
    dialog = window.privacy_dialog
    try:
        dialog.reject()
        dialog.close()
        assert dialog.isVisible()
    finally:
        gate.set()
        qtbot.waitUntil(lambda: dialog.close_button.isEnabled(), timeout=10000)
    assert 'Nenhum metadado' in dialog.heading.text()
    dialog.close()
