"""Permanent opaque redaction of an oriented pixel snapshot, without metadata."""
from pathlib import Path
import warnings
from PIL import Image, ImageOps
from .cleaning import save_pixels


def load_pixels(path: Path) -> Image.Image:
    """Decode once: preview and export use the same EXIF-oriented snapshot."""
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError('Imagens animadas ou com várias páginas não são suportadas.')
            source.load()
            image = ImageOps.exif_transpose(source).convert('RGBA')
            return Image.frombytes('RGBA', image.size, image.tobytes())


def export_redacted(image: Image.Image, regions: tuple, destination: Path, stem: str) -> Path:
    """Replace selected pixels with opaque black and save a new lossless PNG.

    Regions are integer (left, top, right, bottom) boxes, right/bottom exclusive,
    in oriented source coordinates. Reject invalid boxes before creating files.
    The source snapshot remains untouched. No reversible layers are exported.
    """
    if not regions:
        raise ValueError('Marque pelo menos uma região para ocultar.')
    for box in regions:
        if len(box) != 4 or not all(type(value) is int for value in box):
            raise ValueError('Região inválida.')
        left, top, right, bottom = box
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise ValueError('Região fora dos limites da imagem.')
    clean = Image.frombytes('RGBA', image.size, image.convert('RGBA').tobytes())
    for box in regions:
        clean.paste((0, 0, 0, 255), box)
    return save_pixels(clean, Path(stem).name + '_oculta', Path(destination), 'PNG')
