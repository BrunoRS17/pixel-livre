"""Sequential batches with cooperative cancellation and typed progress results."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from .cleaning import clean_image


@dataclass(frozen=True)
class ImageResult:
    index: int
    source: Path
    output: Path | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchSummary:
    saved: int
    failed: int
    skipped: int


def run_batch(
    paths: Sequence[Path], destination: Path, output_format: str, cancel: Event,
    on_started: Callable[[int], None], on_result: Callable[[ImageResult], None],
) -> BatchSummary:
    """Finish the current image on cancellation; isolate failures per input."""
    saved = failed = 0
    for index, source in enumerate(paths):
        if cancel.is_set():
            break
        on_started(index)
        try:
            output = clean_image(source, destination, output_format)
            result = ImageResult(index, source, output=output)
            saved += 1
        except Exception as error:
            result = ImageResult(index, source, error=str(error))
            failed += 1
        on_result(result)
    return BatchSummary(saved, failed, len(paths) - saved - failed)
