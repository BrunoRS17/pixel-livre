"""Optional tests of the distributed binary, independent of an installed Python."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest
from pixel_livre import __version__

pytestmark = pytest.mark.packaged


@pytest.fixture
def executable(tmp_path):
    configured = os.environ.get('PIXEL_LIVRE_EXE')
    if not configured:
        pytest.skip('Set PIXEL_LIVRE_EXE to the built PixelLivre.exe to test the package.')
    source = Path(configured).resolve()
    assert source.is_file(), f'Executable does not exist: {source}'
    destination = tmp_path / 'pasta portátil com espaços'
    destination.mkdir()
    target = destination / 'PixelLivre.exe'
    shutil.copy2(source, target)
    return target


@pytest.mark.parametrize('qt_platform', ['offscreen', 'windows'])
def test_standalone_export_without_python_on_path(executable, tmp_path, qt_platform):
    """The subprocess only receives the EXE; no project/venv is in its working dir."""
    report_dir = tmp_path / f'resultado-{qt_platform}'
    # os.environ is case-insensitive on Windows; a copied dict is not.
    environment = {name.upper(): value for name, value in os.environ.items()}
    for name in ('PYTHONHOME', 'PYTHONPATH', 'VIRTUAL_ENV', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
        environment.pop(name, None)
    environment['PATH'] = str(Path(environment['SYSTEMROOT']) / 'System32')
    environment['QT_QPA_PLATFORM'] = qt_platform
    environment['PYTHONNOUSERSITE'] = '1'
    runtime_temp = tmp_path / 'runtime-temp'
    runtime_temp.mkdir()
    environment['TEMP'] = str(runtime_temp)
    environment['TMP'] = str(runtime_temp)
    # Native Windows plugin is also loaded; the automated window remains hidden.
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    startup = subprocess.STARTUPINFO() if os.name == 'nt' else None
    if startup is not None:
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    # Use a file rather than pipes so a crashed bootloader child cannot keep
    # communicate() blocked. Kill only this test's process tree on timeout.
    with (tmp_path / 'startup.log').open('wb') as log:
        process = subprocess.Popen(
            [str(executable), '--self-test-dir', str(report_dir)],
            cwd=executable.parent, env=environment,
            creationflags=flags, startupinfo=startup, stdout=log, stderr=log,
        )
        try:
            returncode = process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            subprocess.run(
                [str(Path(environment['SYSTEMROOT']) / 'System32' / 'taskkill.exe'),
                 '/PID', str(process.pid), '/T', '/F'],
                check=False, capture_output=True,
            )
            process.wait(timeout=10)
            pytest.fail('Packaged application did not finish within 90 seconds.')
    assert (report_dir / 'report.json').is_file(), (tmp_path / 'startup.log').read_bytes()
    report = json.loads((report_dir / 'report.json').read_text(encoding='utf-8'))
    assert returncode == 0, report
    assert report['success'] is True, report
    assert report['frozen'] is True
    assert report['version'] == __version__
    assert set(report['checks']) == {
        'codec-png', 'codec-jpeg', 'codec-webp', 'original-preserved',
        'qt-window', 'preview', 'gui-worker-export', 'preferences', 'privacy-dialog',
    }
    assert (report_dir / 'window.png').stat().st_size > 0
    assert (report_dir / 'privacy.png').stat().st_size > 0


def test_release_archive_and_checksums():
    configured = os.environ.get('PIXEL_LIVRE_EXE')
    if not configured:
        pytest.skip('Set PIXEL_LIVRE_EXE to validate the release files.')
    executable = Path(configured).resolve()
    archive = executable.parent / f'Pixel-Livre-{__version__}-windows-x64.zip'
    checksums = executable.parent / 'SHA256SUMS.txt'
    expected = dict(line.split('  ', 1)[::-1] for line in checksums.read_text().splitlines())
    for path in (executable, archive):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[path.name]
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert {'PixelLivre.exe', 'LEIA-ME.txt', 'BUILD-INFO.txt'} <= set(names)
        assert any(name.startswith('LICENSES/PySide6-Essentials/') for name in names)
        assert 'LICENSES/Python/LICENSE.txt' in names
        assert hashlib.sha256(bundle.read('PixelLivre.exe')).hexdigest() == expected[executable.name]
    # PE machine field: AMD64, not a Python script or a 32-bit executable.
    binary = executable.read_bytes()
    assert binary[:2] == b'MZ'
    pe_offset = int.from_bytes(binary[0x3c:0x40], 'little')
    assert binary[pe_offset:pe_offset + 6] == b'PE\x00\x00\x64\x86'
