"""High-level panel interface: takes the two rendered PIL layers and flashes them."""

import logging

from . import render as render_mod

logger = logging.getLogger(__name__)

# The render canvas is in reading orientation (300x400); the panel buffer is
# native 400x300. 90 = CCW: the canvas's top edge lands on the panel's native
# LEFT edge (panel mounted short-edge-down, native-left up). Use 270 if the
# mount ends up flipped the other way.
BUFFER_ROTATE_DEG = 90

PANEL_W, PANEL_H = 400, 300


def _to_buffer(img):
    if BUFFER_ROTATE_DEG:
        img = img.rotate(BUFFER_ROTATE_DEG, expand=True)
    if img.size != (PANEL_W, PANEL_H):
        raise ValueError(f"buffer image is {img.size}, panel needs {(PANEL_W, PANEL_H)}")
    return img


def flash(black_img, red_img) -> None:
    """Full-refresh the panel (~15s). Caller is responsible for change-detection."""
    from . import epd as epd_mod

    black_img = _to_buffer(black_img)
    red_img = _to_buffer(red_img)

    panel = epd_mod.EPD()
    try:
        panel.init()
        panel.display(black_img.tobytes(), red_img.tobytes())
        panel.sleep()
        logger.info("panel refreshed")
    finally:
        panel.close()


def flash_value(days: int, last_event_date=None, battery_pct=None) -> None:
    black_img, red_img = render_mod.render(days, last_event_date, battery_pct)
    flash(black_img, red_img)
