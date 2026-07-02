"""High-level panel interface: takes the two rendered PIL layers and flashes them."""

import logging

from . import render as render_mod

logger = logging.getLogger(__name__)

ROTATE_180 = False  # flip if the case mounts the panel upside down


def flash(black_img, red_img) -> None:
    """Full-refresh the panel (~15s). Caller is responsible for change-detection."""
    from . import epd as epd_mod

    if ROTATE_180:
        black_img = black_img.rotate(180)
        red_img = red_img.rotate(180)

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
