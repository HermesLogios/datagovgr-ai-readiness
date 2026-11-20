"""Drawings of the page as inline SVG.

The line icons are those of the Lucide set (ISC licence, web/assets/icons-LICENSE.txt). The status
icons, the icons of the bands of the second reading and the mark of the tool are drawn here. Each
status and each band has its own shape, so that it is told apart without colour; the colour comes
from the stylesheet through currentColor. The mark is a gauge of readiness; web/icon_images.py
makes its PNG and ICO copies from the same measures.
"""
import math

LINE_ICONS = {
    "external-link": '<path d="M15 3h6v6" /><path d="M10 14 21 3" /><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />',
    "download": '<path d="M12 15V3" /><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" />',
    "file-spreadsheet": '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" /><path d="M14 2v5a1 1 0 0 0 1 1h5" /><path d="M8 13h2" /><path d="M14 13h2" /><path d="M8 17h2" /><path d="M14 17h2" />',
    "file-text": '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" /><path d="M14 2v5a1 1 0 0 0 1 1h5" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" />',
    "braces": '<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1" /><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1" />',
    "chevron-down": '<path d="m6 9 6 6 6-6" />',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />',
    "landmark": '<path d="M10 18v-7" /><path d="M11.119 2.205a2 2 0 0 1 1.762 0l7.84 3.846A.5.5 0 0 1 20.5 7h-17a.5.5 0 0 1-.22-.949z" /><path d="M14 18v-7" /><path d="M18 18v-7" /><path d="M3 22h18" /><path d="M6 18v-7" />',
    "calendar-days": '<path d="M8 2v3" /><path d="M16 2v3" /><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18" /><path d="M8 13h.01" /><path d="M12 13h.01" /><path d="M16 13h.01" /><path d="M8 17h.01" /><path d="M12 17h.01" /><path d="M16 17h.01" />',
    "badge-check": '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m16 9-5.5 5.5L8 12" />',
    "code-xml": '<path d="m18 16 4-4-4-4" /><path d="m6 8-4 4 4 4" /><path d="m14.5 4-5 16" />',
    "info": '<circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" />',
    "check": '<path d="M20 6 9 17l-5-5" />',
    "x": '<path d="M18 6 6 18" /><path d="m6 6 12 12" />',
    "search": '<path d="m21 21-4.34-4.34" /><circle cx="11" cy="11" r="8" />',
    "history": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l4 2" />',
    "key-round": '<path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z" /><circle cx="16.5" cy="7.5" r=".5" fill="currentColor" />',
    "text-search": '<path d="M21 5H3" /><path d="M10 12H3" /><path d="M10 19H3" /><circle cx="17" cy="15" r="3" /><path d="m21 19-1.9-1.9" />',
}

WHITE_STROKE = 'fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
RING = 'cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"'
STATUS_DRAWINGS = {
    "met": f'<circle cx="12" cy="12" r="10" fill="currentColor" /><path d="m7.4 12.5 3.1 3.1 6.1-6.7" {WHITE_STROKE} />',
    "partly": f'<circle {RING} /><path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" />',
    "not_met": f'<circle cx="12" cy="12" r="10" fill="currentColor" /><path d="m8.6 8.6 6.8 6.8m0-6.8-6.8 6.8" {WHITE_STROKE} />',
    "not_measured": f'<circle {RING} stroke-dasharray="3.4 3.1" /><path d="M8.5 12h7" fill="none" stroke="currentColor" '
                    'stroke-width="2.2" stroke-linecap="round" />',
    "not_judged": f'<circle {RING} stroke-dasharray="3.4 3.1" /><circle cx="12" cy="12" r="2.3" fill="currentColor" />',
}

# Bands of the second reading, drawn on the dark panel: a full disc, a half disc and an empty ring.
DARK_STROKE = 'fill="none" stroke="#0D1B3E" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
BAND_DRAWINGS = {
    "likely": f'<circle cx="12" cy="12" r="10" fill="currentColor" /><path d="m7.4 12.5 3.1 3.1 6.1-6.7" {DARK_STROKE} />',
    "unsure": f'<circle {RING} /><path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" />',
    "unlikely": f'<circle {RING} /><path d="M8.5 12h7" fill="none" stroke="currentColor" stroke-width="2.2" '
                'stroke-linecap="round" />',
}

# Mark of the tool: a gauge of readiness on a grid of 32 by 32. Three arcs stand for the three scores
# of a criterion (0, 1 and 2), from the dim arc on the left to the bright arc on the right, and a gold
# needle points into the bright arc. Angles are in degrees, from three o'clock, anticlockwise.
NAVY, GOLD = "#0D1B3E", "#F59E0B"
TILE_RADIUS = 7
GAUGE_CENTRE = (16, 17.5)
GAUGE_RADIUS, GAUGE_WIDTH = 10.5, 3.6
GAUGE_ARCS = (("#5B6B94", 210), ("#0891B2", 127), ("#22B8D6", 44))   # colour and angle where the arc starts
GAUGE_ARC_SPAN = 74
NEEDLE_ANGLE, NEEDLE_LENGTH, NEEDLE_WIDTH = 38, 7.6, 2.6
HUB_RADIUS = 2.6
SVG_ATTRIBUTES = 'aria-hidden="true" focusable="false"'


def line_icon(name: str) -> str:
    """Line icon of the Lucide set, in the colour of the text around it."""
    return (f'<svg class="icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {SVG_ATTRIBUTES}>{LINE_ICONS[name]}</svg>')


def status_icon(status_key: str) -> str:
    """Icon of a status; the word of the status always stands next to it."""
    return (f'<svg class="status-icon status-icon--{status_key}" viewBox="0 0 24 24" width="24" height="24" '
            f'{SVG_ATTRIBUTES}>{STATUS_DRAWINGS[status_key]}</svg>')


def band_icon(band: str) -> str:
    """Icon of a band of the second reading; the words of the band always stand next to it."""
    return (f'<svg class="band-icon band-icon--{band}" viewBox="0 0 24 24" width="24" height="24" '
            f'{SVG_ATTRIBUTES}>{BAND_DRAWINGS[band]}</svg>')


def gauge_point(angle: float, distance: float) -> tuple[float, float]:
    """Point of the grid at a distance from the centre of the gauge, rounded to two decimals."""
    radians = math.radians(angle)
    x, y = GAUGE_CENTRE
    return round(x + distance * math.cos(radians), 2), round(y - distance * math.sin(radians), 2)


def mark_drawing() -> str:
    """Arcs, needle and hub of the gauge, drawn in this order."""
    shapes = []
    for colour, start in GAUGE_ARCS:
        x1, y1 = gauge_point(start, GAUGE_RADIUS)
        x2, y2 = gauge_point(start - GAUGE_ARC_SPAN, GAUGE_RADIUS)
        shapes.append(f'<path d="M{x1:g} {y1:g}A{GAUGE_RADIUS:g} {GAUGE_RADIUS:g} 0 0 1 {x2:g} {y2:g}" fill="none" '
                      f'stroke="{colour}" stroke-width="{GAUGE_WIDTH:g}" />')
    x, y = GAUGE_CENTRE
    tip_x, tip_y = gauge_point(NEEDLE_ANGLE, NEEDLE_LENGTH)
    shapes.append(f'<path d="M{x:g} {y:g}L{tip_x:g} {tip_y:g}" stroke="{GOLD}" stroke-width="{NEEDLE_WIDTH:g}" '
                  f'stroke-linecap="round" />')
    shapes.append(f'<circle cx="{x:g}" cy="{y:g}" r="{HUB_RADIUS:g}" fill="{GOLD}" />')
    return "".join(shapes)


def mark_icon() -> str:
    """Mark of the tool next to its name, on the dark header."""
    return f'<svg class="brand-mark" viewBox="0 0 32 32" width="32" height="32" {SVG_ATTRIBUTES}>{mark_drawing()}</svg>'


def favicon_svg() -> str:
    """The mark on a dark rounded tile, as the icon of the browser tab."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            f'<rect width="32" height="32" rx="{TILE_RADIUS}" fill="{NAVY}" />{mark_drawing()}</svg>\n')
