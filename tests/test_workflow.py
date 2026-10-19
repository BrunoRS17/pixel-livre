"""Import policy and batch behavior tested without starting the GUI."""
from pathlib import Path
from threading import Event
from pixel_livre.core.importing import collect_images
from pixel_livre.core.batch import run_batch


def test_folder_import_filters_and_deduplicates(tmp_path, image_factory):
    source = image_factory('ação teste.PNG')
    (tmp_path / 'document.txt').write_text('not an image')
    (tmp_path / 'nested').mkdir()
    result = collect_images([tmp_path, source])
    assert result.paths == [source]
    assert result.ignored == 3
    assert not collect_images([source], [source]).paths


def test_missing_file_ignored(tmp_path):
    result = collect_images([tmp_path / 'missing.png'])
    assert result.paths == []
    assert result.ignored == 1


def test_unreadable_directory_reported(tmp_path, monkeypatch):
    def denied(self):
        raise PermissionError('access denied')
    monkeypatch.setattr(Path, 'iterdir', denied)
    result = collect_images([tmp_path])
    assert result.paths == []
    assert 'access denied' in result.errors[0]


def test_cancel_finishes_current_image_only(tmp_path, image_factory):
    first, second = image_factory('a.png'), image_factory('b.png')
    cancel = Event()
    results = []
    def received(result):
        results.append(result)
        cancel.set()
    summary = run_batch([first, second], tmp_path / 'out', 'PNG', cancel, lambda _: None, received)
    assert (summary.saved, summary.skipped) == (1, 1)
    assert results[0].output.is_file()
    assert not (tmp_path / 'out' / 'b_limpa.png').exists()


def test_cancel_before_start_does_not_write(tmp_path, image_factory):
    cancel = Event()
    cancel.set()
    events = []
    summary = run_batch([image_factory()], tmp_path / 'out', 'PNG', cancel, events.append, events.append)
    assert (summary.saved, summary.failed, summary.skipped) == (0, 0, 1)
    assert not events
    assert not (tmp_path / 'out').exists()


def test_error_does_not_abort_remaining_images(tmp_path, image_factory):
    broken = tmp_path / 'bad.png'
    broken.write_bytes(b'broken')
    results = []
    summary = run_batch([broken, image_factory()], tmp_path / 'out', 'PNG', Event(), lambda _: None, results.append)
    assert (summary.saved, summary.failed) == (1, 1)
    assert results[0].error
    assert results[1].output.is_file()


def test_invalid_destination_reported_without_overwrite(image_factory):
    source = image_factory()
    original = source.read_bytes()
    results = []
    summary = run_batch([source], source, 'PNG', Event(), lambda _: None, results.append)
    assert summary.failed == 1
    assert source.read_bytes() == original


def test_empty_batch(tmp_path):
    events = []
    summary = run_batch([], tmp_path / 'out', 'PNG', Event(), events.append, events.append)
    assert (summary.saved, summary.failed, summary.skipped) == (0, 0, 0)
    assert events == []
