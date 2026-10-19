from pathlib import Path
import tempfile
import unittest

from PIL import Image, PngImagePlugin

from cleaner import clean_image


class CleaningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_png_metadata_alpha_and_original(self):
        source = self.root / 'foto.png'
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('Author', 'Private author')
        metadata.add_text('XML:com.adobe.xmp', '<private/>')
        Image.new('RGBA', (8, 6), (25, 50, 75, 128)).save(source, pnginfo=metadata)
        before = source.read_bytes()
        target = clean_image(source, self.root)
        with Image.open(target) as result:
            self.assertEqual(result.info, {})
            self.assertEqual(result.getpixel((0, 0)), (25, 50, 75, 128))
        self.assertEqual(source.read_bytes(), before)
        second = clean_image(source, self.root)
        self.assertNotEqual(target, second)
        self.assertTrue(target.exists())

    def test_exif_orientation(self):
        source = self.root / 'foto.jpg'
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = 'Private author'
        Image.new('RGB', (10, 20), 'red').save(source, exif=exif)
        for output_format in ('PNG', 'JPEG', 'WEBP'):
            target = clean_image(source, self.root, output_format)
            with Image.open(target) as result:
                self.assertEqual(result.size, (20, 10))
                self.assertFalse(result.getexif())
                self.assertNotIn('exif', result.info)
                self.assertNotIn('xmp', result.info)

    def test_palette_transparency(self):
        source = self.root / 'palette.png'
        image = Image.new('P', (4, 4), 0)
        image.save(source, transparency=0)
        target = clean_image(source, self.root)
        with Image.open(target) as result:
            self.assertEqual(result.getpixel((0, 0))[3], 0)

    def test_jpeg_white_background(self):
        source = self.root / 'alpha.png'
        Image.new('RGBA', (4, 4), (0, 0, 0, 0)).save(source)
        target = clean_image(source, self.root, 'JPEG')
        with Image.open(target) as result:
            self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))

    def test_animation_and_corrupt_file_rejected(self):
        source = self.root / 'animation.png'
        Image.new('RGB', (4, 4), 'red').save(source, save_all=True, append_images=[Image.new('RGB', (4, 4), 'blue')])
        with self.assertRaises(ValueError):
            clean_image(source, self.root / 'output')
        broken = self.root / 'broken.png'
        broken.write_bytes(b'not an image')
        with self.assertRaises(OSError):
            clean_image(broken, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
