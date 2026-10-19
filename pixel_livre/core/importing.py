"""One input policy for dialogs and drag-and-drop."""
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Iterable
from .cleaning import SUPPORTED


@dataclass
class ImportResult:
    paths: list[Path] = field(default_factory=list)
    ignored: int = 0
    errors: list[str] = field(default_factory=list)


def collect_images(inputs: Iterable[str | Path], existing: Iterable[Path] = ()) -> ImportResult:
    """Expand one directory level and deduplicate; decoding happens during cleaning."""
    result = ImportResult()
    known = {p.resolve() for p in existing}
    for value in inputs:
        try:
            source = Path(value).expanduser().resolve()
            candidates = sorted(source.iterdir()) if source.is_dir() else [source]
            for path in candidates:
                path = path.resolve()
                if path.is_file() and path.suffix.lower() in SUPPORTED and path not in known:
                    known.add(path)
                    result.paths.append(path)
                else:
                    result.ignored += 1
        except (OSError, ValueError) as error:
            result.errors.append(f'{value}: {error}')
    return result
