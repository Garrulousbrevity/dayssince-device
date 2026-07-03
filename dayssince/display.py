"""High-level panel interface: takes the rendered PIL layers and flashes them."""

import logging

from . import config, render as render_mod

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


def flash_pair(layers) -> None:
    """Flash [left, right] layer pairs onto both panels, refreshing in
    parallel (~15s total, not 2×): one shared reset, init both, load both,
    kick both refreshes, then wait for both BUSYs."""
    from . import epd as epd_mod

    bufs = [(_to_buffer(b).tobytes(), _to_buffer(r).tobytes()) for b, r in layers]
    if config.PANEL_SWAP:
        bufs.reverse()

    rst, dc = epd_mod.shared_lines()
    panels = []
    try:
        epd_mod.reset_shared(rst)
        for spi_cs, busy_pin, variant_env in (
            (0, epd_mod.BUSY_PIN, "DAYSSINCE_EPD_VARIANT"),
            (1, epd_mod.BUSY2_PIN, "DAYSSINCE_EPD_VARIANT2"),
        ):
            panel = epd_mod.EPD(spi_cs=spi_cs, busy_pin=busy_pin, rst=rst, dc=dc,
                                variant_env=variant_env)
            panel.init(reset=False)
            panels.append(panel)
        for panel, (black_buf, red_buf) in zip(panels, bufs):
            panel.load(black_buf, red_buf)
        for panel in panels:
            panel.start_refresh()
        for panel in panels:
            panel.wait_refresh()
        for panel in panels:
            panel.sleep()
        logger.info("both panels refreshed")
    finally:
        for panel in panels:
            panel.close()


def flash_value(days: int, last_event=None, battery_pct=None, reporter=None) -> None:
    if config.PANELS >= 2:
        flash_pair(render_mod.render_pair(days, last_event, battery_pct, reporter,
                                          layout=config.LAYOUT))
    else:
        last_event_date = (last_event or "")[:10] or None
        black_img, red_img = render_mod.render(days, last_event_date, battery_pct)
        flash(black_img, red_img)
