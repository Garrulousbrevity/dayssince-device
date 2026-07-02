"""Persistent device state (survives the off-time between wakes)."""

import json
import logging
import os

from . import config

logger = logging.getLogger(__name__)

DEFAULTS = {
    "last_drawn_value": None,   # daysSince value currently on the panel
    "last_update_date": None,   # "YYYY-MM-DD" of the last git pull
    "battery_log": [],          # recent [iso_timestamp, pct] samples for drain analysis
}


def load() -> dict:
    try:
        with open(config.STATE_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError) as err:
        logger.info("no usable state file (%s), starting fresh", err)
        return dict(DEFAULTS)


def save(state: dict) -> None:
    os.makedirs(os.path.dirname(config.STATE_PATH), exist_ok=True)
    tmp = config.STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, config.STATE_PATH)


def log_battery(state: dict, iso_now: str, pct: float, keep: int = 200) -> None:
    state["battery_log"] = (state.get("battery_log") or [])[-(keep - 1):] + [[iso_now, pct]]
