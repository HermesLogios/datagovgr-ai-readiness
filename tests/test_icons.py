"""The mark of the tool, its icon for the browser tab and its PNG and ICO copies."""
import math
import re
import struct
import unittest
import zlib

from web import icon_images, icons

CENTRE, RADIUS = (16, 17.5), 10.5
NAVY, GOLD, BRIGHT_TEAL = (0x0D, 0x1B, 0x3E), (0xF5, 0x9E, 0x0B), (0x22, 0xB8, 0xD6)
ARC = re.compile(r'<path d="M([\d.]+) ([\d.]+)A10\.5 10\.5 0 0 1 ([\d.]+) ([\d.]+)" fill="none" '
                 r'stroke="(#[0-9A-F]{6})" stroke-width="3\.6" />')
NEEDLE = re.compile(r'<path d="M16 17\.5L([\d.]+) ([\d.]+)" stroke="#F59E0B" stroke-width="2\.6" stroke-linecap="round" />')


def angle_of(x: float, y: float) -> float:
    """Angle of a point of the grid around the centre of the gauge, in degrees from three o'clock, anticlockwise."""
    return math.degrees(math.atan2(CENTRE[1] - y, x - CENTRE[0])) % 360


def read_png(data: bytes):
    """Width, height and rows of RGBA pixels of a PNG with 8-bit RGBA rows and no row filters."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    position, header, compressed = 8, b"", b""
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            header = body
        elif kind == b"IDAT":
            compressed += body
        position += 12 + length
    width, height, depth, colour_type = struct.unpack(">IIBB", header[:10])
    if (depth, colour_type) != (8, 6):
        raise ValueError("not 8-bit RGBA")
    raw = zlib.decompress(compressed)
    stride = 1 + 4 * width
    rows = [raw[row * stride:(row + 1) * stride] for row in range(height)]
    if any(row[0] != 0 for row in rows):
        raise ValueError("row filters are not expected")
    return width, height, [[tuple(row[1 + 4 * x:5 + 4 * x]) for x in range(width)] for row in rows]


class MarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mark = icons.mark_icon()
        cls.arcs = ARC.findall(cls.mark)

    def test_mark_is_three_arcs_of_a_gauge_from_dim_to_bright_and_no_cells(self):
        self.assertTrue(self.mark.startswith('<svg class="brand-mark" viewBox="0 0 32 32" width="32" height="32" '
                                             'aria-hidden="true" focusable="false">'))
        self.assertEqual([arc[4] for arc in self.arcs], ["#5B6B94", "#0891B2", "#22B8D6"])
        self.assertNotIn("<rect", self.mark)

    def test_arcs_lie_on_one_circle_with_equal_spans_and_equal_gaps(self):
        ends = []
        for x1, y1, x2, y2, _ in self.arcs:
            for x, y in ((float(x1), float(y1)), (float(x2), float(y2))):
                self.assertAlmostEqual(math.dist((x, y), CENTRE), RADIUS, delta=0.01)
            ends.append((angle_of(float(x1), float(y1)), angle_of(float(x2), float(y2))))
        for start, end in ends:
            self.assertAlmostEqual((start - end) % 360, 74, delta=0.1)
        for earlier, later in zip(ends, ends[1:]):
            self.assertAlmostEqual((earlier[1] - later[0]) % 360, 9, delta=0.1)
        self.assertAlmostEqual(ends[0][0], 210, delta=0.1)
        self.assertAlmostEqual(ends[-1][1], 330, delta=0.1)

    def test_gold_needle_with_its_hub_points_into_the_bright_arc(self):
        needle = NEEDLE.search(self.mark)
        self.assertIsNotNone(needle)
        tip = (float(needle[1]), float(needle[2]))
        self.assertLessEqual((44 - angle_of(*tip)) % 360, 74)
        self.assertAlmostEqual(math.dist(tip, CENTRE), 7.6, delta=0.01)
        self.assertIn('<circle cx="16" cy="17.5" r="2.6" fill="#F59E0B" />', self.mark)
        self.assertLess(self.mark.index("<path d=\"M16 17.5L"), self.mark.index("<circle"))

    def test_icon_of_the_tab_is_the_mark_on_the_dark_rounded_tile(self):
        favicon = icons.favicon_svg()
        self.assertTrue(favicon.startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
                                           '<rect width="32" height="32" rx="7" fill="#0D1B3E" />'))
        self.assertIn(icons.mark_drawing(), favicon)
        self.assertIn(icons.mark_drawing(), self.mark)


class RasterIconTest(unittest.TestCase):
    def test_icon_of_phones_is_an_opaque_square_of_180_pixels_with_the_mark(self):
        width, height, pixels = read_png(icon_images.touch_icon_png())
        self.assertEqual((width, height), (180, 180))
        self.assertTrue(all(pixel[3] == 255 for row in pixels for pixel in row))
        scale = 180 / 32
        self.assertEqual(pixels[0][0][:3], NAVY)
        self.assertEqual(pixels[int(17.5 * scale)][int(16 * scale)][:3], GOLD)
        self.assertEqual(pixels[int(17.5 * scale)][int(26.5 * scale)][:3], BRIGHT_TEAL)

    def test_icon_of_old_browsers_holds_pngs_of_16_and_32_pixels(self):
        data = icon_images.favicon_ico()
        self.assertEqual(struct.unpack("<HHH", data[:6]), (0, 1, 2))
        sizes = []
        for index in range(2):
            width, height, _, _, planes, bits, length, offset = struct.unpack(
                "<BBBBHHII", data[6 + 16 * index:22 + 16 * index])
            png_width, png_height, _ = read_png(data[offset:offset + length])
            self.assertEqual((png_width, png_height, planes, bits), (width, height, 1, 32))
            sizes.append(width)
        self.assertEqual(sizes, [16, 32])

    def test_icon_of_old_browsers_keeps_the_rounded_tile_and_the_gold_hub(self):
        data = icon_images.favicon_ico()
        _, _, _, _, _, _, length, offset = struct.unpack("<BBBBHHII", data[22:38])
        _, _, pixels = read_png(data[offset:offset + length])
        self.assertEqual(pixels[0][0][3], 0)
        self.assertEqual(pixels[16][1], NAVY + (255,))
        self.assertEqual(pixels[17][16], GOLD + (255,))


if __name__ == "__main__":
    unittest.main()
