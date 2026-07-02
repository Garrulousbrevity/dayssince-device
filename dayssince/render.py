"""Render the 400x300 display layout as separate black and red 1-bit layers.

Iterate on this via `dayssince.py --png out.png --value N` — never on the
panel itself (each panel refresh is a ~15s flash and wears the display).
"""

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 400, 300

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_BOLD = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
FONT_REGULAR = f"{FONT_DIR}/DejaVuSans.ttf"

BLACK, WHITE = 0, 1


def _fit_font(path: str, text: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > 10:
        font = ImageFont.truetype(path, size)
        if font.getbbox(text)[2] <= max_width:
            return font
        size -= 4
    return ImageFont.truetype(path, 10)


def render(days: int, last_event_date: str | None = None, battery_pct: float | None = None):
    """Return (black_layer, red_layer) as mode-'1' images, white background."""
    black_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    red_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    black = ImageDraw.Draw(black_img)
    red = ImageDraw.Draw(red_img)

    # Frame
    black.rectangle([2, 2, WIDTH - 3, HEIGHT - 3], outline=BLACK, width=3)

    # Header
    header_font = _fit_font(FONT_BOLD, "DAYS SINCE MENTIONING", WIDTH - 40, 30)
    black.text((WIDTH // 2, 38), "DAYS SINCE MENTIONING", font=header_font, fill=BLACK, anchor="mm")

    name_font = _fit_font(FONT_BOLD, "WAYFAIR", WIDTH - 60, 52)
    red.text((WIDTH // 2, 85), "WAYFAIR", font=name_font, fill=BLACK, anchor="mm")

    # The big number — red on a fresh reset (0), black otherwise
    number = str(days)
    number_font = _fit_font(FONT_BOLD, number, WIDTH - 60, 150)
    target = red if days == 0 else black
    target.text((WIDTH // 2, 185), number, font=number_font, fill=BLACK, anchor="mm")

    # Footer
    footer_font = ImageFont.truetype(FONT_REGULAR, 16)
    if last_event_date:
        black.text((14, HEIGHT - 22), f"since {last_event_date}", font=footer_font, fill=BLACK, anchor="lm")
    if battery_pct is not None:
        black.text((WIDTH - 14, HEIGHT - 22), f"bat {battery_pct:.0f}%", font=footer_font, fill=BLACK, anchor="rm")

    return black_img, red_img


def composite(black_img: Image.Image, red_img: Image.Image) -> Image.Image:
    """Merge the two layers into an RGB preview image (for --png)."""
    out = Image.new("RGB", (WIDTH, HEIGHT), "white")
    px_out = out.load()
    px_black = black_img.load()
    px_red = red_img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if px_red[x, y] == 0:
                px_out[x, y] = (200, 30, 30)
            elif px_black[x, y] == 0:
                px_out[x, y] = (0, 0, 0)
    return out
