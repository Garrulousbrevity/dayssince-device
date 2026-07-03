"""Central configuration for the DaysSince device."""

import os

GRAPHQL_ENDPOINT = "https://dayssince.garrulousbrevity.com/graphql"
EVENT_NAME = "Wayfair"

# Display: 1 = original single panel, 2 = two panels / two digits (tens panel
# shows a leading 0 under 10). Two-panel since 2026-07-03.
PANELS = int(os.environ.get("DAYSSINCE_PANELS", "2"))
# Footer composition for the two-panel layout: corners | centered | stacked
# (see render.render_pair).
LAYOUT = os.environ.get("DAYSSINCE_LAYOUT", "corners")
# The original panel (CE0) renders the LEFT half; set DAYSSINCE_PANEL_SWAP=1
# if the physical mounting ends up mirrored.
PANEL_SWAP = os.environ.get("DAYSSINCE_PANEL_SWAP", "") not in ("", "0")

# Battery (field) schedule: wake on quarter-hour wall-clock slots within this window.
ACTIVE_START_HOUR = 9   # first slot 09:00
ACTIVE_END_HOUR = 17    # last slot 17:00 (inclusive)

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
