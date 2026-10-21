"""Limpeza local de metadados, sem modificar o arquivo de origem."""
from pathlib import Path
import warnings

from PIL import Image, ImageOps

SUPPORTED = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}


def clean_image(source: Path, destination: Path, output_format: str = 'PNG') -> Path:
    """Write a metadata-free pixel copy and return its exclusively reserved path.

    Apply EXIF orientation first. Preserve alpha except for JPEG (white matte).
    Never overwrite an existing file; remove a partial output if encoding fails.
    Multiframe inputs are rejected rather than silently losing pages or frames.
    """
    source, destination = Path(source), Path(destination)
    if output_format not in {'PNG', 'JPEG', 'WEBP'}:
        raise ValueError('Formato de saída inválido.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(source) as original:
            if getattr(original, 'n_frames', 1) != 1:
                raise ValueError('Imagens animadas ou com várias páginas não são suportadas.')
            original.load()
            oriented = ImageOps.exif_transpose(original)
            alpha = 'A' in oriented.getbands() or 'transparency' in oriented.info
            converted = oriented.convert('RGBA' if alpha else 'RGB')
            if output_format == 'JPEG' and alpha:
                background = Image.new('RGB', converted.size, 'white')
                background.paste(converted, mask=converted.getchannel('A'))
                converted = background
            # Copiar apenas os pixels impede a propagação de EXIF, XMP e outros campos.
            clean = Image.frombytes(converted.mode, converted.size, converted.tobytes())
    return save_pixels(clean, source.stem + '_limpa', destination, output_format)


def save_pixels(clean: Image.Image, stem: str, destination: Path, output_format: str) -> Path:
    """Save owned pixel image exclusively; always close it, removing failed output."""
    destination.mkdir(parents=True, exist_ok=True)
    extension = {'PNG': '.png', 'JPEG': '.jpg', 'WEBP': '.webp'}[output_format]
    options = {'quality': 95, 'subsampling': 0} if output_format == 'JPEG' else {}
    if output_format == 'WEBP':
        options = {'lossless': True}
    index = 0
    while True:
        suffix = '' if index == 0 else f'_{index}'
        target = destination / f'{stem}{suffix}{extension}'
        try:
            handle = target.open('xb')
            break
        except FileExistsError:
            index += 1
    try:
        with handle:
            clean.save(handle, format=output_format, **options)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        clean.close()
    return target
