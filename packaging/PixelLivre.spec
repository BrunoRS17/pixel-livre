# PyInstaller one-file Windows build, deliberately without UPX or elevation.
from pathlib import Path
import os
import sys

root = Path(SPECPATH).parent
sys.path.insert(0, str(root))
from pixel_livre import __version__

analysis = Analysis(
    [str(root / 'app.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'pytestqt', 'coverage'],
    noarchive=False,
)
archive = PYZ(analysis.pure)
exe = EXE(
    archive, analysis.scripts, analysis.binaries, analysis.datas, [],
    name='PixelLivreDebug' if os.environ.get('PIXEL_LIVRE_DEBUG') == '1' else 'PixelLivre',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=os.environ.get('PIXEL_LIVRE_DEBUG') == '1',
    disable_windowed_traceback=False,
    version=str(root / 'build' / 'windows-version.txt'),
    uac_admin=False,
)
