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
