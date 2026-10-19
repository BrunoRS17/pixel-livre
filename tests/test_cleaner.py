"""Image-level regression tests: metadata, pixels, orientation and safe writes."""
import pytest
from PIL import Image, PngImagePlugin
from pixel_livre.core.cleaning import clean_image


def test_png_metadata_alpha_and_original(tmp_path, image_factory):
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('Author', 'Private author')
    metadata.add_text('XML:com.adobe.xmp', '<private/>')
    source = image_factory(pnginfo=metadata)
    before = source.read_bytes()
    target = clean_image(source, tmp_path)
    with Image.open(target) as result:
        assert result.info == {}
        assert result.getpixel((0, 0)) == (20, 60, 120, 128)
    assert source.read_bytes() == before


@pytest.mark.parametrize('output_format', ['PNG', 'JPEG', 'WEBP'])
def test_exif_orientation_and_removal(tmp_path, image_factory, output_format):
    exif = Image.Exif()
    exif[274] = 6
    exif[315] = 'Private author'
    source = image_factory('foto.jpg', mode='RGB', color='red', exif=exif)
    target = clean_image(source, tmp_path, output_format)
    with Image.open(target) as result:
        assert result.size == (20, 40)
        assert not result.getexif()
        assert not {'exif', 'xmp', 'icc_profile'} & result.info.keys()


def test_palette_transparency(tmp_path):
    source = tmp_path / 'palette.png'
    Image.new('P', (4, 4), 0).save(source, transparency=0)
    with Image.open(clean_image(source, tmp_path)) as result:
        assert result.getpixel((0, 0))[3] == 0


def test_jpeg_white_background(tmp_path, image_factory):
    source = image_factory(color=(0, 0, 0, 0))
    with Image.open(clean_image(source, tmp_path, 'JPEG')) as result:
        assert result.getpixel((0, 0)) == (255, 255, 255)


def test_animation_rejected_before_creating_output(tmp_path):
    source = tmp_path / 'animation.png'
    Image.new('RGB', (4, 4), 'red').save(source, save_all=True,
        append_images=[Image.new('RGB', (4, 4), 'blue')])
    with pytest.raises(ValueError, match='animadas'):
        clean_image(source, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_corrupt_input_rejected(tmp_path):
    source = tmp_path / 'broken.png'
    source.write_bytes(b'not an image')
    with pytest.raises(OSError):
        clean_image(source, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_existing_outputs_never_overwritten(tmp_path, image_factory):
    source = image_factory('photo.png')
    original = source.read_bytes()
    existing = tmp_path / 'photo_limpa.png'
    existing.write_bytes(b'preserve me')
    first = clean_image(source, tmp_path)
    second = clean_image(source, tmp_path)
    assert first.name == 'photo_limpa_1.png'
    assert second.name == 'photo_limpa_2.png'
    assert existing.read_bytes() == b'preserve me'
    assert source.read_bytes() == original


@pytest.mark.parametrize('invalid_format', ['GIF', '', 'png'])
def test_invalid_format_rejected(tmp_path, image_factory, invalid_format):
    source = image_factory()
    with pytest.raises(ValueError, match='Formato'):
        clean_image(source, tmp_path / 'out', invalid_format)
    assert not (tmp_path / 'out').exists()


def test_encoding_failure_removes_only_partial_output(tmp_path, image_factory, monkeypatch):
    source = image_factory()
    original = source.read_bytes()
    def fail_save(self, stream, **kwargs):
        stream.write(b'partial')
        raise OSError('encoder failure')
    monkeypatch.setattr(Image.Image, 'save', fail_save)
    destination = tmp_path / 'out'
    with pytest.raises(OSError, match='encoder failure'):
        clean_image(source, destination)
    assert list(destination.iterdir()) == []
    assert source.read_bytes() == original
