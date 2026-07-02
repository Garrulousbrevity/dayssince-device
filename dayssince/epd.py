"""Driver for the Waveshare 4.2" B/W/Red e-paper module (bare SPI, rev 2.2).

Adapted from Waveshare's epd4in2b_V2.py (MIT-licensed, see vendor/ for the
original). Differences from upstream:

- Pure Python: hardware SPI via spidev + GPIO via gpiozero. Upstream V4.1
  depends on a precompiled DEV_Config .so (built for ARMv7, which SIGSEGVs on
  the Pi Zero W's ARMv6) purely so it can *read* the controller version over
  the shared data line. We avoid the read entirely:
- Controller variant (SSD1683 vs UC8176 — rev 2.2 panels ship with either) is
  detected from the BUSY pin's idle level after hardware reset: SSD1683 idles
  low, UC8176 idles high. Override with DAYSSINCE_EPD_VARIANT=ssd1683|uc8176
  if the heuristic ever guesses wrong (symptom: BusyTimeout or a blank flash).
- BUSY waits have a timeout instead of hanging forever.
- Buffers are packed with PIL's tobytes() instead of a per-pixel Python loop
  (the loop takes ~10s per layer on an ARMv6 core).
"""

import logging
import os
import time

logger = logging.getLogger(__name__)

WIDTH, HEIGHT = 400, 300
BYTES = WIDTH * HEIGHT // 8

RST_PIN = 17
DC_PIN = 25
BUSY_PIN = 24

SSD1683 = "ssd1683"
UC8176 = "uc8176"


class BusyTimeout(Exception):
    pass


class EPD:
    def __init__(self):
        import gpiozero
        import spidev

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # CE0 handles chip-select in hardware
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0b00
        self.rst = gpiozero.LED(RST_PIN)
        self.dc = gpiozero.LED(DC_PIN)
        self.busy = gpiozero.Button(BUSY_PIN, pull_up=False)
        self.variant = None

    def _reset(self):
        self.rst.on()
        time.sleep(0.2)
        self.rst.off()
        time.sleep(0.005)
        self.rst.on()
        time.sleep(0.3)

    def _command(self, cmd):
        self.dc.off()
        self.spi.writebytes([cmd])

    def _data(self, data):
        self.dc.on()
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            self.spi.writebytes2(data)

    def _wait_idle(self, timeout=60.0):
        busy_level = 1 if self.variant == SSD1683 else 0
        deadline = time.monotonic() + timeout
        while self.busy.value == busy_level:
            if time.monotonic() > deadline:
                raise BusyTimeout(f"panel busy for >{timeout}s (variant={self.variant})")
            time.sleep(0.05)

    def init(self):
        self._reset()
        override = os.environ.get("DAYSSINCE_EPD_VARIANT")
        if override in (SSD1683, UC8176):
            self.variant = override
        else:
            self.variant = SSD1683 if self.busy.value == 0 else UC8176
        logger.info("panel variant: %s%s", self.variant, " (env override)" if override else "")

        if self.variant == SSD1683:
            self._wait_idle()
            self._command(0x12)  # software reset
            self._wait_idle()
            self._command(0x3C)  # border waveform
            self._data(0x05)
            self._command(0x18)  # internal temp sensor
            self._data(0x80)
            self._command(0x11)  # data entry mode
            self._data(0x03)
            self._command(0x44)  # X window
            self._data(0x00)
            self._data(WIDTH // 8 - 1)
            self._command(0x45)  # Y window
            self._data(0x00)
            self._data(0x00)
            self._data((HEIGHT - 1) % 256)
            self._data((HEIGHT - 1) // 256)
            self._command(0x4E)  # X counter
            self._data(0x00)
            self._command(0x4F)  # Y counter
            self._data(0x00)
            self._data(0x00)
            self._wait_idle()
        else:
            self._command(0x04)  # power on
            self._wait_idle()
            self._command(0x00)  # panel setting
            self._data(0x0F)

    def _refresh(self):
        if self.variant == SSD1683:
            self._command(0x22)
            self._data(0xF7)
            self._command(0x20)
        else:
            self._command(0x12)
            time.sleep(0.1)
        self._wait_idle(timeout=60.0)

    def display(self, black_buf: bytes, red_buf: bytes):
        """Buffers are packed 1bpp, bit 1 = white/no-red (PIL '1' tobytes())."""
        if len(black_buf) != BYTES or len(red_buf) != BYTES:
            raise ValueError(f"buffers must be {BYTES} bytes")
        red_inverted = bytes(b ^ 0xFF for b in red_buf)
        self._command(0x24 if self.variant == SSD1683 else 0x10)
        self._data(black_buf)
        self._command(0x26 if self.variant == SSD1683 else 0x13)
        self._data(red_inverted)
        self._refresh()

    def clear(self):
        self._command(0x24 if self.variant == SSD1683 else 0x10)
        self._data(bytes([0xFF] * BYTES))
        self._command(0x26 if self.variant == SSD1683 else 0x13)
        self._data(bytes([0x00] * BYTES))
        self._refresh()

    def sleep(self):
        if self.variant == SSD1683:
            self._command(0x10)
            self._data(0x03)
        else:
            self._command(0x50)
            self._data(0xF7)
            self._command(0x02)
            self._wait_idle()
            self._command(0x07)
            self._data(0xA5)
        time.sleep(0.1)

    def close(self):
        self.spi.close()
        self.rst.off()
        self.dc.off()
