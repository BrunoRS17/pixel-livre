"""Build a portable Windows executable and ZIP from an isolated environment.

Run with the interpreter that has requirements-build.txt installed.
No credentials, source checkout, user preferences or tests are packaged.
"""
import hashlib
import os
from importlib import metadata
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixel_livre import __version__


def main() -> None:
    if sys.platform != 'win32' or platform.machine().lower() not in {'amd64', 'x86_64'}:
        raise SystemExit('Build this package on 64-bit Windows with x64 Python.')
    if platform.architecture()[0] != '64bit':
        raise SystemExit('A 64-bit Python interpreter is required.')
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    version = tuple(int(part) for part in __version__.split('.')) + (0,)
    (build / 'windows-version.txt').write_text(f"""
VSVersionInfo(
  ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('ProductName', 'Pixel Livre'),
    StringStruct('FileDescription', 'Pixel Livre - limpeza local de metadados'),
    StringStruct('FileVersion', '{__version__}'),
    StringStruct('ProductVersion', '{__version__}'),
    StringStruct('OriginalFilename', 'PixelLivre.exe')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
""", encoding='utf-8')
    # Do not collect unrelated DLLs from other tools installed on the build host.
    # In particular, a third-party ICU DLL can shadow the Windows ICU used by Qt.
    environment = {name.upper(): value for name, value in os.environ.items()}
    for name in ('PYTHONPATH', 'PYTHONHOME', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'PIXEL_LIVRE_DEBUG'):
        environment.pop(name, None)
    windows = Path(environment['SYSTEMROOT'])
    environment['PATH'] = os.pathsep.join(
        str(path) for path in (Path(sys.executable).parent, Path(sys.base_prefix), windows / 'System32', windows)
    )
    environment['PYINSTALLER_CONFIG_DIR'] = str(build / 'pyinstaller-cache')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm',
                    str(ROOT / 'packaging' / 'PixelLivre.spec')], cwd=ROOT, env=environment, check=True)
    executable = ROOT / 'dist' / 'PixelLivre.exe'
    archive = ROOT / 'dist' / f'Pixel-Livre-{__version__}-windows-x64.zip'
    instructions = (
        f'Pixel Livre {__version__} - Windows x64\n\n'
        'Extraia todo o ZIP em uma pasta e abra PixelLivre.exe.\n'
        'Nao e necessario instalar Python. Nao execute como administrador.\n'
        'Arraste imagens para a area tracejada, escolha a pasta de saida e clique em Limpar imagens.\n'
        'Os originais sao preservados. A primeira abertura pode levar alguns segundos.\n'
        'Este executavel nao tem assinatura digital de editor.\n\n'
        'Codigo-fonte e instrucoes: https://github.com/BrunoRS17/pixel-livre\n'
        'Licencas de componentes de terceiros: pasta LICENSES neste ZIP.\n'
    )
    manifest = {'Python': platform.python_version()}
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(executable, 'PixelLivre.exe')
        bundle.writestr('LEIA-ME.txt', instructions)
        for package in ('Pillow', 'PySide6-Essentials', 'shiboken6', 'PyInstaller', 'pyinstaller-hooks-contrib'):
            distribution = metadata.distribution(package)
            manifest[package] = distribution.version
            for file in distribution.files or ():
                if any(part.lower().startswith(('license', 'copying', 'notice')) for part in file.parts):
                    source = Path(distribution.locate_file(file))
                    if source.is_file():
                        bundle.write(source, str(Path('LICENSES') / package / file))
        python_license = Path(sys.base_prefix) / 'LICENSE.txt'
        if not python_license.is_file():
            raise RuntimeError('Python LICENSE.txt was not found; do not distribute without it.')
        bundle.write(python_license, 'LICENSES/Python/LICENSE.txt')
        bundle.writestr('BUILD-INFO.txt', '\n'.join(f'{key}=={value}' for key, value in manifest.items()) + '\n')
    checksums = ROOT / 'dist' / 'SHA256SUMS.txt'
    checksums.write_text('\n'.join(
        f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}'
        for path in (archive, executable)
    ) + '\n', encoding='ascii')
    print(f'Built {archive.name} ({archive.stat().st_size / 1024 / 1024:.1f} MB)')


if __name__ == '__main__':
    main()
