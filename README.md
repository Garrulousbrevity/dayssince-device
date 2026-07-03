# dayssince-device

Firmware for a battery-powered e-ink sign that shows **"Days Since Mentioning
Wayfair"**, replacing the whiteboard version of the joke. Data comes from the
public GraphQL endpoint at `dayssince.garrulousbrevity.com` (resets happen via
the web UI at `wayfair.garrulousbrevity.com`).

## Hardware

- Raspberry Pi Zero W (rev 1.1, ARMv6 — see the ARMv6 notes below)
- Waveshare 4.2" 400×300 black/white/red e-Paper module, bare SPI, rev 2.2
- PiSugar 3 (1200 mAh battery + RTC, I2C `0x57`/`0x68`)

### Panel wiring (8-pin cable → Pi header)

| Panel wire | Color  | Physical pin | BCM |
|-----------|--------|--------------|-----|
| VCC       | grey   | 17 (3.3V)    | —   |
| GND       | brown  | 20           | —   |
| DIN       | blue   | 19 (MOSI)    | 10  |
| CLK       | yellow | 23 (SCLK)    | 11  |
| CS        | orange | 24 (CE0)     | 8   |
| DC        | green  | 22           | 25  |
| RST       | white  | 11           | 17  |
| BUSY      | purple | 18           | 24  |

### Panel 2 wiring (second 4.2" module)

DIN/CLK/DC/RST are shared with panel 1 via 1-female-to-2-male splitters
(female end on the header pin, both panels' same-color wires on the male
ends). DC is only sampled by the panel whose CS is active; a shared RST
resets both panels at once, which the driver expects — one reset pulse, then
both panels are initialized without re-pulsing. CS and BUSY must be unique
per panel; VCC/GND take spare header pins, no splitter needed.

Full header map (pin 1 = the **square solder pad** at the SD-card end of the
board, on the row toward the board's interior; odd pins = inner row, even
pins = board-edge row). P1/P2 = panel 1/panel 2 cable, colors are the
Waveshare loom:

| Pin | Name         | Connection                       |     | Pin | Name         | Connection                       |
|----:|--------------|----------------------------------|-----|----:|--------------|----------------------------------|
| 1   | 3.3V         | **P2 VCC** (grey)                |     | 2   | 5V           | — (PiSugar power, pogo pads)     |
| 3   | GPIO2 (SDA)  | — keep free (PiSugar I2C)        |     | 4   | 5V           | — (PiSugar power)                |
| 5   | GPIO3 (SCL)  | — keep free (PiSugar I2C)        |     | 6   | GND          | — (PiSugar ground)               |
| 7   | GPIO4        | —                                |     | 8   | GPIO14 (TXD) | —                                |
| 9   | GND          | —                                |     | 10  | GPIO15 (RXD) | —                                |
| 11  | GPIO17       | **SPLIT — RST** P1+P2 (white)    |     | 12  | GPIO18       | —                                |
| 13  | GPIO27       | —                                |     | 14  | GND          | —                                |
| 15  | GPIO22       | —                                |     | 16  | GPIO23       | **P2 BUSY** (purple)             |
| 17  | 3.3V         | **P1 VCC** (grey)                |     | 18  | GPIO24       | **P1 BUSY** (purple)             |
| 19  | GPIO10 (MOSI)| **SPLIT — DIN** P1+P2 (blue)     |     | 20  | GND          | **P1 GND** (brown)               |
| 21  | GPIO9 (MISO) | — (e-ink is write-only)          |     | 22  | GPIO25       | **SPLIT — DC** P1+P2 (green)     |
| 23  | GPIO11 (SCLK)| **SPLIT — CLK** P1+P2 (yellow)   |     | 24  | GPIO8 (CE0)  | **P1 CS** (orange)               |
| 25  | GND          | **P2 GND** (brown)               |     | 26  | GPIO7 (CE1)  | **P2 CS** (orange)               |
| 27  | ID_SD        | — reserved, never use            |     | 28  | ID_SC        | — reserved, never use            |
| 29  | GPIO5        | —                                |     | 30  | GND          | —                                |
| 31  | GPIO6        | —                                |     | 32  | GPIO12       | —                                |
| 33  | GPIO13       | —                                |     | 34  | GND          | —                                |
| 35  | GPIO19       | —                                |     | 36  | GPIO16       | —                                |
| 37  | GPIO26       | —                                |     | 38  | GPIO20       | —                                |
| 39  | GND          | —                                |     | 40  | GPIO21       | —                                |

## How it behaves

The Pi is **off** almost all the time; the e-ink panel holds its image at 0 W.
`launcher.py` runs once per boot (systemd `dayssince.service`) and branches on
whether external power is connected (PiSugar `battery_power_plugged`):

- **Battery (field mode)**: arm the next PiSugar RTC alarm *first* (crash-safe),
  then once a day `git pull`, fetch `daysSince`, re-flash the panel **only if
  the value changed** (a full refresh takes ~15 s and wears the panel), and
  shut down. Wakes land on wall-clock quarter-hours (:00/:15/:30/:45) between
  09:00 and 17:00; overnight it sleeps until 09:00.
- **Plugged (dev/watch mode)**: stay up, poll every 60 s, `git pull` every
  5 min (re-exec on new code), and listen on `:8321` for a webhook poke that
  triggers an immediate pull. Unplugging drops straight into field mode.

Power-on from full shutdown: **tap the PiSugar button** (requires
`anti_mistouch false`, set by install.sh), or feed micro-USB directly into the
Pi's own PWR port. Note the charger alone does NOT power it on once
pisugar-poweroff has cut output, and `auto_power_on` must stay false — the
firmware refuses RTC alarms while it's enabled. While running: double-tap
re-runs the launcher ("update now"); if external power is present at boot the
launcher stays up in watch mode, so "plug it in, tap the button" is the
enter-dev-mode gesture.

**Emergency hold**: `touch /boot/firmware/dayssince-hold` (from SSH, or by
mounting the SD card) makes the launcher exit without flashing or shutting
down.

## Install

Flash Raspberry Pi OS Lite (32-bit), configure WiFi + SSH, then:

```bash
sudo apt-get install -y git
git clone https://github.com/Garrulousbrevity/dayssince-device.git
cd dayssince-device
sudo ./install.sh
```

The repo is public and read-only on the device — there are no secrets here;
the GraphQL read requires no auth.

## Dev loop

Iterate the layout as a PNG — never on the panel:

```bash
./dayssince.py --png /tmp/preview.png --value 42   # then scp it somewhere and look
./dayssince.py --panel --value 42                  # flash the real panel once
./dayssince.py --once                              # exactly what a field wake does
journalctl -u dayssince -f                         # watch the launcher
```

While plugged in, pushes to `main` reach the device within ~5 min (or seconds,
via the dayssince-server /device-poke webhook). On battery, new code goes live at the
next 09:00 wake.

## ARMv6 notes (Pi Zero W)

- **pisugar-server**: the `armhf` debs are built for ARMv7 and crash with
  SIGSEGV on the Zero W. Install the statically linked **`armel`** debs
  (install.sh does). Everything else about the PiSugar API is unchanged.
- **e-paper driver**: `dayssince/epd.py` is a pure-Python adaptation of
  Waveshare's `epd4in2b_V2.py` (original in `vendor/`). Upstream needs a
  precompiled ARMv7 `.so` just to read the controller ID; we instead detect
  the controller (SSD1683 vs UC8176) from the BUSY pin's idle level, with a
  `DAYSSINCE_EPD_VARIANT=ssd1683|uc8176` env override.
- Python deps are apt packages only (`python3-pil`, `python3-requests`,
  `python3-spidev`, `python3-gpiozero`, `python3-lgpio`) — no pip, no wheels.

## Tuning levers

All in `dayssince/config.py`, deployed like code: active hours, watch
interval, pull cadence. Battery drain is logged to the state file
(`/var/lib/dayssince/state.json`) as `battery_log` for measuring real-world
life.

## Tests

```bash
python3 -m unittest discover tests
```
