"""Read-only, local metadata inspection. Findings are evidence, not a safety score."""
from dataclasses import dataclass
from pathlib import Path
import warnings

from PIL import ExifTags, Image


@dataclass(frozen=True)
class Finding:
    category: str
    field: str
    value: str
    explanation: str


@dataclass(frozen=True)
class PrivacyReport:
    findings: tuple[Finding, ...]
    warnings: tuple[str, ...] = ()


LIMITATIONS = ('A análise cobre metadados reconhecidos pelo Pillow, na primeira imagem/página. '
               'Não verifica rostos, textos visíveis, dados ocultos nos pixels ou credenciais C2PA. '
               'Nenhum achado não significa anonimato garantido.')


def readable(value: object) -> str:
    """Bound display size and remove control characters from untrusted metadata."""
    if isinstance(value, bytes):
        return f'Bloco binário · {len(value)} bytes'
    text = str(value)
    return ''.join(c if c.isprintable() else ' ' for c in text[:500]) + ('…' if len(text) > 500 else '')


def classify(name: str) -> tuple[str, str]:
    key = name.lower()
    if any(word in key for word in ('gps', 'location', 'latitude', 'longitude')):
        return 'Localização', 'Pode revelar onde a imagem foi registrada.'
    if any(word in key for word in ('artist', 'author', 'owner', 'copyright', 'serial')):
        return 'Identificação', 'Pode identificar uma pessoa, autoria ou um aparelho.'
    if any(word in key for word in ('date', 'time')):
        return 'Data e horário', 'Pode revelar quando a imagem foi criada ou editada.'
    if any(word in key for word in ('make', 'model', 'software', 'lens')):
        return 'Dispositivo e software', 'Pode revelar o equipamento ou aplicativo utilizado.'
    return 'Outros metadados', 'Revise o conteúdo antes de compartilhar.'


def inspect_privacy(path: Path) -> PrivacyReport:
    """Inspect without writing, logging, networking or interpreting XML payloads.

    A malformed metadata section yields an incomplete report. An unreadable image
    raises an exception so callers never present a false clean result.
    """
    findings: list[Finding] = []
    notices: list[str] = []

    def add(name, value, category=None, explanation=None):
        group, reason = classify(name)
        findings.append(Finding(category or group, readable(name), readable(value), explanation or reason))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as image:
            image.load()  # PNG may store text and EXIF after image data.
            if getattr(image, 'n_frames', 1) > 1:
                notices.append('Arquivo com várias imagens: apenas a primeira foi analisada.')
            try:
                exif = image.getexif()
                for tag, value in exif.items():
                    if tag not in (34665, 34853):
                        add(ExifTags.TAGS.get(tag, f'EXIF {tag}'), value)
                for pointer, gps in ((34665, False), (34853, True)):
                    if pointer in exif:
                        nested = exif.get_ifd(pointer)
                        if not nested:
                            notices.append('Um bloco EXIF não pôde ser interpretado.')
                        for tag, value in nested.items():
                            name = (ExifTags.GPSTAGS if gps else ExifTags.TAGS).get(tag, str(tag))
                            add('GPS / ' + name if gps else name, value)
            except Exception:
                notices.append('Leitura EXIF incompleta; alguns campos não puderam ser interpretados.')
            text_fields = getattr(image, 'text', {})
            for name, value in text_fields.items():
                add(name, value, explanation=('Bloco XMP presente; conteúdo exibido sem interpretação.'
                                             if 'xmp' in name.lower() else None))
            for name, value in image.info.items():
                if name in text_fields or name == 'exif':
                    continue
                if name in ('xmp', 'XML:com.adobe.xmp', 'photoshop', 'comment', 'icc_profile'):
                    add(name, value, explanation='Bloco presente; o conteúdo interno não foi interpretado.')
        if caught:
            notices.append('O leitor encontrou avisos no arquivo; a análise pode estar incompleta.')
    return PrivacyReport(tuple(findings), tuple(notices))
