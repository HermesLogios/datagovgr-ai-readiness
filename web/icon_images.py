"""PNG and ICO copies of the mark of the tool, for phones and for browsers that do not show SVG icons.

The shapes and measures are those of web.icons. Each pixel is the average of 4 by 4 samples, so that the
edges stay smooth. The files are written with the standard library alone, because the site is built
without third-party packages.
"""
import functools
import math
import struct
import zlib

from web.icons import (GAUGE_ARC_SPAN, GAUGE_ARCS, GAUGE_CENTRE, GAUGE_RADIUS, GAUGE_WIDTH, GOLD, HUB_RADIUS,
                       NAVY, NEEDLE_ANGLE, NEEDLE_LENGTH, NEEDLE_WIDTH, TILE_RADIUS, gauge_point)

GRID = 32
SAMPLES = 4
TOUCH_ICON_SIZE = 180
FAVICON_SIZES = (16, 32)


def rgb(colour: str) -> tuple[int, int, int]:
    return int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)


ARC_COLOURS = tuple((rgb(colour), start) for colour, start in GAUGE_ARCS)
NAVY_RGB, GOLD_RGB = rgb(NAVY), rgb(GOLD)
NEEDLE_TIP = gauge_point(NEEDLE_ANGLE, NEEDLE_LENGTH)


def distance_to_needle(x: float, y: float) -> float:
    """Distance of a point of the grid from the line of the needle, between the centre and the tip."""
    (x1, y1), (x2, y2) = GAUGE_CENTRE, NEEDLE_TIP
    dx, dy = x2 - x1, y2 - y1
    share = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + share * dx), y - (y1 + share * dy))


def inside_tile(x: float, y: float, rounded: bool) -> bool:
    if not (0 <= x <= GRID and 0 <= y <= GRID):
        return False
    if not rounded:
        return True
    nearest_x = min(max(x, TILE_RADIUS), GRID - TILE_RADIUS)
    nearest_y = min(max(y, TILE_RADIUS), GRID - TILE_RADIUS)
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= TILE_RADIUS ** 2


def colour_at(x: float, y: float, rounded: bool) -> tuple[int, int, int] | None:
    """Colour of the topmost shape at a point of the grid, or None where the tile does not reach."""
    centre_x, centre_y = GAUGE_CENTRE
    across, up = x - centre_x, centre_y - y
    distance = math.hypot(across, up)
    if distance <= HUB_RADIUS or distance_to_needle(x, y) <= NEEDLE_WIDTH / 2:
        return GOLD_RGB
    if abs(distance - GAUGE_RADIUS) <= GAUGE_WIDTH / 2:
        angle = math.degrees(math.atan2(up, across))
        for colour, start in ARC_COLOURS:
            if (start - angle) % 360 <= GAUGE_ARC_SPAN:
                return colour
    return NAVY_RGB if inside_tile(x, y, rounded) else None


def pixel_rows(size: int, rounded: bool) -> list[bytes]:
    """Rows of RGBA pixels of the mark on its tile, at a size in pixels."""
    scale = GRID / size
    offsets = [(step + 0.5) / SAMPLES for step in range(SAMPLES)]
    rows = []
    for row in range(size):
        pixels = bytearray()
        for column in range(size):
            red = green = blue = covered = 0
            for offset_y in offsets:
                y = (row + offset_y) * scale
                for offset_x in offsets:
                    colour = colour_at((column + offset_x) * scale, y, rounded)
                    if colour:
                        red, green, blue, covered = red + colour[0], green + colour[1], blue + colour[2], covered + 1
            if covered:
                pixels += bytes((round(red / covered), round(green / covered), round(blue / covered),
                                 round(255 * covered / SAMPLES ** 2)))
            else:
                pixels += bytes(4)
        rows.append(bytes(pixels))
    return rows


def png_chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


@functools.cache
def mark_png(size: int, rounded: bool) -> bytes:
    """The mark as a PNG of 8-bit RGBA pixels, rows written without filters."""
    raw = b"".join(b"\x00" + row for row in pixel_rows(size, rounded))
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(raw, 9))
            + png_chunk(b"IEND", b""))


def touch_icon_png() -> bytes:
    """Icon of the site on the home screen of a phone: an opaque square, since phones round the corners."""
    return mark_png(TOUCH_ICON_SIZE, rounded=False)


def favicon_ico() -> bytes:
    """Icon of the tab for browsers without SVG icons: the rounded tile at 16 and 32 pixels, as PNG inside ICO."""
    images = [mark_png(size, rounded=True) for size in FAVICON_SIZES]
    entries, offset = b"", 6 + 16 * len(images)
    for size, image in zip(FAVICON_SIZES, images):
        entries += struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(image), offset)
        offset += len(image)
    return struct.pack("<HHH", 0, 1, len(images)) + entries + b"".join(images)
