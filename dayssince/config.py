"""Central configuration for the DaysSince device."""

GRAPHQL_ENDPOINT = "https://dayssince.garrulousbrevity.com/graphql"
EVENT_NAME = "Wayfair"

# Battery (field) schedule: wake on quarter-hour wall-clock slots within this window.
# TEMP for overnight field-mode testing 2026-07-02: window widened to all day so
# self-wakes can be observed immediately. Revert to 9/17 after the test.
ACTIVE_START_HOUR = 0   # first slot 09:00
ACTIVE_END_HOUR = 23    # last slot 17:00 (inclusive)

# Plugged (dev/watch) mode
WATCH_INTERVAL_SECONDS = 60
WATCH_PULL_INTERVAL_SECONDS = 300  # git pull every ~5 min while plugged
WEBHOOK_PORT = 8321  # any POST here (LAN only) triggers an immediate pull

# Minimum seconds of headroom when picking the next RTC alarm, so a slot that's
# about to pass isn't scheduled while we're still shutting down.
ALARM_MARGIN_SECONDS = 90

STATE_PATH = "/var/lib/dayssince/state.json"

PISUGAR_HOST = "127.0.0.1"
PISUGAR_PORT = 8423
