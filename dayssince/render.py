"""Render the display layout as separate black and red 1-bit layers.

The canvas is in READING orientation (300x400 — the panel is mounted on its
short edge, native-left up); display.py rotates it into the panel's native
400x300 buffer. The layout is deliberately minimal: the whiteboard already
says "Days since mentioning Wayfair" — this is just where the number goes,
readable from across the room.

Iterate on this via `dayssince.py --png out.png --value N` — never on the
panel itself (each panel refresh is a ~15s flash and wears the display).
"""

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 300, 400

# Bump when the layout changes: forces a re-flash even if the number hasn't
# moved (change-detection otherwise skips identical values).
RENDER_VERSION = 4

import os


def _first_font(*paths: str) -> str:
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"none of the candidate fonts exist: {paths}")


# Fira Code to match the garrulousbrevity.com theme; DejaVu as fallback.
FONT_BOLD = _first_font(
    "/usr/share/fonts/truetype/firacode/FiraCode-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
FONT_REGULAR = _first_font(
    "/usr/share/fonts/truetype/firacode/FiraCode-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

BLACK, WHITE = 0, 1


def _fit_font(path: str, text: str, max_width: int, max_height: int, start_size: int, stroke: int = 0):
    size = start_size
    while size > 10:
        font = ImageFont.truetype(path, size)
        left, top, right, bottom = font.getbbox(text, stroke_width=stroke)
        if right - left <= max_width and bottom - top <= max_height:
            return font
        size -= 6
    return ImageFont.truetype(path, 10)


def render(days: int, last_event_date: str | None = None, battery_pct: float | None = None):
    """Return (black_layer, red_layer) as mode-'1' images, white background."""
    black_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    red_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    black = ImageDraw.Draw(black_img)
    red = ImageDraw.Draw(red_img)

    # The number, as big as it fits: red fill (red layer) + black outline
    # (black layer) — reads at a distance against any background.
    number = str(days)
    stroke = 8
    # Size against all-zeros of the same digit count (the widest case) so every
    # value with N digits renders at the same, maximal scale.
    number_font = _fit_font(FONT_BOLD, "0" * len(number), WIDTH - 8, HEIGHT - 50, 560, stroke=stroke)
    center = (WIDTH // 2, (HEIGHT - 30) // 2)
    red.text(center, number, font=number_font, fill=BLACK, anchor="mm")
    black.text(center, number, font=number_font, fill=WHITE, anchor="mm",
               stroke_width=stroke, stroke_fill=BLACK)

    # Footer small print
    footer_font = ImageFont.truetype(FONT_REGULAR, 16)
    if last_event_date:
        black.text((10, HEIGHT - 14), f"since {last_event_date}", font=footer_font, fill=BLACK, anchor="lm")
    if battery_pct is not None:
        black.text((WIDTH - 10, HEIGHT - 14), f"{battery_pct:.0f}%", font=footer_font, fill=BLACK, anchor="rm")

    return black_img, red_img


def composite(black_img: Image.Image, red_img: Image.Image) -> Image.Image:
    """Merge the two layers into an RGB preview image (for --png)."""
    out = Image.new("RGB", black_img.size, "white")
    px_out = out.load()
    px_black = black_img.load()
    px_red = red_img.load()
    w, h = black_img.size
    for y in range(h):
        for x in range(w):
            if px_red[x, y] == 0:
                px_out[x, y] = (200, 30, 30)
            elif px_black[x, y] == 0:
                px_out[x, y] = (0, 0, 0)
    return out
