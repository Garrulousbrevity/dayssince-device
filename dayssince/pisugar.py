"""Minimal client for the pisugar-server TCP API (port 8423).

Verified against pisugar-server 2.3.2 / PiSugar 3 firmware v1.3.4:
- `get battery_power_plugged` -> "battery_power_plugged: true"
- `rtc_alarm_set <ISO8601+offset> <weekday_mask>` -> "rtc_alarm_set: done"
  The RTC stores only time-of-day + weekday repeat (the date reads back as
  1999-12-31); with mask 127 the alarm fires at the next occurrence of that
  time, which is always correct for wakes scheduled within 24h.
"""

import logging
import socket
from datetime import datetime

from . import config

logger = logging.getLogger(__name__)


class PiSugarError(Exception):
    pass


def _command(cmd: str, timeout: float = 5.0) -> str:
    with socket.create_connection((config.PISUGAR_HOST, config.PISUGAR_PORT), timeout=timeout) as sock:
        sock.sendall(cmd.encode() + b"\n")
        sock.settimeout(timeout)
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(1024)
            if not chunk:
                break
            data += chunk
    reply = data.decode().strip()
    logger.debug("pisugar: %s => %s", cmd, reply)
    return reply


def _get(field: str) -> str:
    reply = _command(f"get {field}")
    prefix = f"{field}: "
    if not reply.startswith(prefix):
        raise PiSugarError(f"unexpected reply to 'get {field}': {reply!r}")
    return reply[len(prefix):]


def power_plugged() -> bool:
    return _get("battery_power_plugged") == "true"


def battery_pct() -> float:
    return float(_get("battery"))


def sync_rtc_from_pi() -> None:
    reply = _command("rtc_pi2rtc")
    if "done" not in reply:
        raise PiSugarError(f"rtc_pi2rtc failed: {reply!r}")


def sync_pi_from_rtc() -> None:
    reply = _command("rtc_rtc2pi")
    if "done" not in reply:
        raise PiSugarError(f"rtc_rtc2pi failed: {reply!r}")


def set_next_alarm(when: datetime) -> None:
    """Arm the single RTC alarm slot for `when` (must be tz-aware, within 24h)."""
    if when.tzinfo is None:
        raise ValueError("alarm datetime must be timezone-aware")
    iso = when.strftime("%Y-%m-%dT%H:%M:%S%z")
    iso = iso[:-2] + ":" + iso[-2:]  # +0400 -> +04:00
    reply = _command(f"rtc_alarm_set {iso} 127")
    if "done" not in reply:
        raise PiSugarError(f"rtc_alarm_set failed: {reply!r}")
    logger.info("next RTC wake armed for %s", iso)
