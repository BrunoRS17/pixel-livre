"""Opt-in packaged smoke test. Never runs during normal application startup.

Uses only synthetic files and an isolated INI. Requiring a new directory prevents
accidentally overwriting user data. The JSON report is consumed by pytest.
"""
import json
from pathlib import Path
import sys

from PIL import Image, PngImagePlugin
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from . import __version__
from .core.cleaning import clean_image
from .settings import Preferences
from .ui.theme import STYLESHEET
from .ui.window import MainWindow


def run_self_test(directory: str) -> int:
    """Verify bundled encoders and the actual Qt window/worker, then exit."""
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    report = {
        'version': __version__, 'frozen': bool(getattr(sys, 'frozen', False)),
        'checks': [], 'success': False,
    }
    app = None
    window = None
    privacy_dialog = None
    redaction_dialog = None
    privacy_checked = False
    redaction_started = False
    try:
        source = root / 'imagem com acentuação.png'
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('Author', 'Synthetic test')
        Image.new('RGBA', (40, 20), (20, 60, 120, 128)).save(source, pnginfo=metadata)
        original_bytes = source.read_bytes()
        for output_format in ('PNG', 'JPEG', 'WEBP'):
            target = clean_image(source, root / output_format, output_format)
            with Image.open(target) as result:
                result.load()
                assert result.size == (40, 20)
                assert not result.getexif()
                assert not {'Author', 'exif', 'xmp', 'icc_profile'} & result.info.keys()
                if output_format != 'JPEG':
                    assert result.getpixel((0, 0)) == (20, 60, 120, 128)
            report['checks'].append(f'codec-{output_format.lower()}')
        assert source.read_bytes() == original_bytes
        report['checks'].append('original-preserved')

        app = QApplication([])
        app.setStyle('Fusion')
        app.setStyleSheet(STYLESHEET)
        settings = Preferences(QSettings(str(root / 'settings.ini'), QSettings.Format.IniFormat))
        window = MainWindow(settings)
        window.show()
        window.add_paths([str(source)])
        window.view.destination.setText(str(root / 'gui-output'))
        finished = False

        def inspect():
            nonlocal finished, privacy_dialog, redaction_dialog, privacy_checked, redaction_started
            if window.busy or finished:
                return
            if privacy_dialog is None:
                window.show_privacy()
                privacy_dialog = window.privacy_dialog
                return
            if not privacy_checked and not privacy_dialog.close_button.isEnabled():
                return
            try:
                if not privacy_checked:
                    assert 'Synthetic test' in privacy_dialog.details.toPlainText()
                    assert 'campo(s)' in privacy_dialog.heading.text()
                    privacy_dialog.grab().save(str(root / 'privacy.png'))
                    privacy_dialog.close()
                    privacy_checked = True
                    report['checks'].append('privacy-dialog')
                    window.show_redaction()
                    redaction_dialog = window.redaction_dialog
                    return
                if redaction_dialog.working:
                    return
                if not redaction_started:
                    assert redaction_dialog.image is not None
                    redaction_dialog.canvas.regions.append((5, 5, 20, 15))
                    redaction_dialog.export_to(str(root / 'redacted'))
                    redaction_started = True
                    return
                assert redaction_dialog.output is not None
                with Image.open(redaction_dialog.output) as redacted:
                    assert redacted.getpixel((10, 10)) == (0, 0, 0, 255)
                    assert redacted.getpixel((30, 18)) == (20, 60, 120, 128)
                    assert not redacted.info
                assert source.read_bytes() == original_bytes
                redaction_dialog.grab().save(str(root / 'redaction.png'))
                redaction_dialog.close()
                report['checks'].append('redaction-export')
                finished = True
                assert (root / 'gui-output' / 'imagem com acentuação_limpa.png').is_file()
                assert '1 salva(s)' in window.view.status.text()
                assert window.view.start.isEnabled()
                assert not window.view.preview.pixmap().isNull()
                assert settings.destination == str(root / 'gui-output')
                window.grab().save(str(root / 'window.png'))
                report['checks'].extend(['qt-window', 'preview', 'gui-worker-export', 'preferences'])
                report['success'] = True
            except Exception as error:
                report['error'] = f'{type(error).__name__}: {error}'
            app.quit()

        def timeout():
            report['error'] = 'Qt processing timed out'
            app.quit()

        timer = QTimer()
        timer.timeout.connect(inspect)
        deadline = QTimer()
        deadline.setSingleShot(True)
        deadline.timeout.connect(timeout)
        window.start_batch()
        timer.start(50)
        deadline.start(30000)
        app.exec()
        timer.stop()
        deadline.stop()
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if privacy_dialog is not None:
            # Retained by the Qt parent until deferred deletion is processed.
            if not privacy_checked:
                privacy_dialog.worker.wait()
                privacy_dialog.close()
        if redaction_dialog is not None and not finished:
            if redaction_dialog.task is not None:
                redaction_dialog.task.wait()
                app.processEvents()
            redaction_dialog.close()
        if window is not None:
            if window.worker is not None:
                window.worker.cancel_requested.set()
                window.worker.wait()
                app.processEvents()
            window.close()
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['success'] else 1
