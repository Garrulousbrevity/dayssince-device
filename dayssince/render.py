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
RENDER_VERSION = 5

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


def _new_canvas():
    black_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    red_img = Image.new("1", (WIDTH, HEIGHT), WHITE)
    return black_img, red_img, ImageDraw.Draw(black_img), ImageDraw.Draw(red_img)


def _draw_number(black, red, number: str, footer_top: int) -> None:
    """The number, as big as it fits above the footer: red fill (red layer) +
    black outline (black layer) — reads at a distance against any background."""
    stroke = 8
    top_margin = 6
    # Size against all-zeros of the same digit count (the widest case) so every
    # value with N digits renders at the same, maximal scale.
    number_font = _fit_font(FONT_BOLD, "0" * len(number), WIDTH - 8,
                            footer_top - top_margin - 6, 560, stroke=stroke)
    # anchor="mm" centers on the em box, but digits sit high in it — measure
    # the actual ink and center that between the top edge and the footer.
    probe = (WIDTH // 2, (top_margin + footer_top) // 2)
    ink = black.textbbox(probe, number, font=number_font, anchor="mm", stroke_width=stroke)
    dy = probe[1] - (ink[1] + ink[3]) // 2
    center = (probe[0], probe[1] + dy)
    red.text(center, number, font=number_font, fill=BLACK, anchor="mm")
    black.text(center, number, font=number_font, fill=WHITE, anchor="mm",
               stroke_width=stroke, stroke_fill=BLACK)


def _event_time(last_event: str | None) -> str | None:
    """'2026-07-01T14:32:05.123Z' -> '2026-07-01 14:32' in local time."""
    if not last_event:
        return None
    if len(last_event) <= 10:
        return last_event
    try:
        from datetime import datetime
        return datetime.fromisoformat(last_event.replace("Z", "+00:00")) \
            .astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return last_event[:16].replace("T", " ")


def render(days: int, last_event_date: str | None = None, battery_pct: float | None = None):
    """Single-panel layout: (black_layer, red_layer) as mode-'1' images."""
    black_img, red_img, black, red = _new_canvas()

    footer_top = HEIGHT - 30
    _draw_number(black, red, str(days), footer_top)

    # Footer small print
    footer_font = ImageFont.truetype(FONT_REGULAR, 16)
    if last_event_date:
        black.text((10, HEIGHT - 14), f"since {last_event_date}", font=footer_font, fill=BLACK, anchor="lm")
    if battery_pct is not None:
        black.text((WIDTH - 10, HEIGHT - 14), f"{battery_pct:.0f}%", font=footer_font, fill=BLACK, anchor="rm")

    return black_img, red_img


# Two-panel footer compositions ("corners" mirrors the single-panel look):
#   corners  — left panel: "since <when>" bottom-left; right panel:
#              "by <who>" bottom-left, "<batt>%" bottom-right
#   centered — one caption centered under each digit: "since <when>" left,
#              "<who> · <batt>%" right
#   stacked  — two footer lines; left panel: "since <when>" over
#              "reported by <who>"; right panel: "<batt>%" bottom-right
LAYOUTS = ("corners", "centered", "stacked")


def render_pair(days: int, last_event: str | None = None, battery_pct: float | None = None,
                reporter: str | None = None, layout: str = "corners"):
    """Two-panel layout: [(black, red), (black, red)] for [left, right].

    The left (tens) panel keeps a leading 0 under 10 so the sign always shows
    two digits. Both panels reserve the same footer height so the digits match.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout {layout!r}, expected one of {LAYOUTS}")
    left_digits = str(days // 10) if days >= 10 else "0"
    right_digit = str(days % 10)
    when = _event_time(last_event)
    batt = f"{battery_pct:.0f}%" if battery_pct is not None else None

    footer_lines = 2 if layout == "stacked" else 1
    footer_top = HEIGHT - 30 * footer_lines
    line1_y = HEIGHT - 14                      # bottom line
    line0_y = HEIGHT - 44                      # upper line (stacked only)

    lb_img, lr_img, lb, lr = _new_canvas()
    rb_img, rr_img, rb, rr = _new_canvas()
    _draw_number(lb, lr, left_digits, footer_top)
    _draw_number(rb, rr, right_digit, footer_top)

    footer_font = ImageFont.truetype(FONT_REGULAR, 16)
    if layout == "corners":
        if when:
            lb.text((10, line1_y), f"since {when}", font=footer_font, fill=BLACK, anchor="lm")
        if reporter:
            rb.text((10, line1_y), f"by {reporter}", font=footer_font, fill=BLACK, anchor="lm")
        if batt:
            rb.text((WIDTH - 10, line1_y), batt, font=footer_font, fill=BLACK, anchor="rm")
    elif layout == "centered":
        if when:
            lb.text((WIDTH // 2, line1_y), f"since {when}", font=footer_font, fill=BLACK, anchor="mm")
        right_bits = " · ".join(bit for bit in (reporter, batt) if bit)
        if right_bits:
            rb.text((WIDTH // 2, line1_y), right_bits, font=footer_font, fill=BLACK, anchor="mm")
    elif layout == "stacked":
        if when:
            lb.text((10, line0_y), f"since {when}", font=footer_font, fill=BLACK, anchor="lm")
        if reporter:
            lb.text((10, line1_y), f"reported by {reporter}", font=footer_font, fill=BLACK, anchor="lm")
        if batt:
            rb.text((WIDTH - 10, line1_y), batt, font=footer_font, fill=BLACK, anchor="rm")

    return [(lb_img, lr_img), (rb_img, rr_img)]


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
