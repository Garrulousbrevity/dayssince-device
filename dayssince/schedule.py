"""Wake schedule policy.

On battery the device wakes on quarter-hour wall-clock slots (:00/:15/:30/:45)
between ACTIVE_START_HOUR:00 and ACTIVE_END_HOUR:00 inclusive, then sleeps
until ACTIVE_START_HOUR:00 the next day. Pure function so it can be unit
tested off-device.
"""

from datetime import datetime, timedelta

from . import config


def next_wake(now: datetime) -> datetime:
    """Return the next scheduled wake time (same tzinfo as `now`)."""
    earliest = now + timedelta(seconds=config.ALARM_MARGIN_SECONDS)

    # Next quarter-hour boundary strictly at/after `earliest`.
    slot = earliest.replace(second=0, microsecond=0)
    remainder = slot.minute % 15
    if remainder or earliest > slot:
        slot += timedelta(minutes=15 - remainder if remainder else 15)

    start = slot.replace(hour=config.ACTIVE_START_HOUR, minute=0)
    end = slot.replace(hour=config.ACTIVE_END_HOUR, minute=0)
    if slot < start:
        return start
    if slot > end:
        return start + timedelta(days=1)
    return slot


def is_alarm_wake(now: datetime, armed_iso: str | None,
                  tolerance_seconds: int = config.ALARM_MATCH_SECONDS,
                  early_seconds: int = 60) -> bool:
    """Did the RTC alarm armed at `armed_iso` plausibly cause a boot at `now`?

    Compares time-of-day only: the PiSugar alarm stores time-of-day + a daily
    repeat, so if re-arming failed the *old* time still fires on later days and
    must still count as an alarm wake. The window is asymmetric — an alarm can't
    boot us before it fires (a small early allowance covers clock slop), but
    boot + network can take a couple of minutes after.
    """
    if not armed_iso:
        return False
    try:
        armed = datetime.fromisoformat(armed_iso)
        delta = (now - armed).total_seconds()
    except (ValueError, TypeError):
        return False
    delta = (delta + 43200) % 86400 - 43200  # wrap into (-12h, +12h]
    return -early_seconds <= delta <= tolerance_seconds
