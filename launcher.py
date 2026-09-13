#!/usr/bin/env python3
"""Boot entrypoint. Decides field mode vs dev mode from external power.

On battery (field mode): arm the next RTC wake FIRST (a crash after that
point still leaves a scheduled wake), refresh the panel if the value changed,
shut down.

On external power (dev/watch mode): stay up, poll every minute, pull new code
every ~5 minutes and re-exec on change. Falls back to field mode the moment
power is unplugged.

Either way, a *manual* start forces a panel redraw even if nothing changed:
a fresh boot that the RTC alarm didn't cause (single tap on battery, USB
power-on) or a service restart on a long-running system (the PiSugar
double-tap gesture while plugged in). Alarm wakes and our own re-execs keep
the change-only rule.
"""

import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from dayssince import config, display, fetch, pisugar, render, schedule, state

REPO_DIR = os.path.dirname(os.path.realpath(__file__))
HOLD_FILE = "/boot/firmware/dayssince-hold"
REEXEC_ENV = "DAYSSINCE_REEXEC"
# A launcher start this long after boot can't be the boot itself. The unit has
# Restart=no, so it means someone restarted the service — in practice the
# PiSugar double-tap (`systemctl restart dayssince`).
BOOT_WINDOW_SECONDS = 300

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("launcher")


def reexec() -> None:
    """Restart the launcher in place (new code, or a field->watch flip).
    Tagged so the next main() knows this is neither a boot nor a button gesture."""
    os.execve(sys.executable, [sys.executable, os.path.realpath(__file__)],
              {**os.environ, REEXEC_ENV: "1"})


def uptime_seconds() -> float:
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def wake_reason(st: dict, now: datetime) -> str:
    """Why is the launcher running?

    reexec  — we re-exec'd ourselves (new code pulled, or field->watch flip)
    restart — service restarted on a long-running system (double-tap gesture)
    alarm   — fresh boot caused by the RTC alarm we armed
    manual  — fresh boot caused by anything else (single tap, USB power-on)
    """
    if os.environ.get(REEXEC_ENV):
        return "reexec"
    try:
        if uptime_seconds() > BOOT_WINDOW_SECONDS:
            return "restart"
    except OSError as err:
        logger.warning("could not read uptime (%s), assuming fresh boot", err)
    # Fresh boot. Two independent signals can attribute it to the alarm: the
    # PiSugar's alarm flag (cleared here so it can't go stale and mask a later
    # tap), and the clock landing just after the wake we armed. Either counts —
    # pisugar-server may clear the flag before we read it, so a false flag
    # alone doesn't prove a manual wake.
    fired = False
    try:
        fired = pisugar.alarm_fired()
        if fired:
            pisugar.clear_alarm_flag()
    except Exception as err:
        logger.warning("alarm flag check failed: %s", err)
    if fired or schedule.is_alarm_wake(now, st.get("next_wake")):
        return "alarm"
    return "manual"


def shutdown():
    logger.info("shutting down")
    cmd = ["shutdown", "-h", "now"]
    if os.geteuid() != 0:
        cmd = ["sudo"] + cmd
    subprocess.run(cmd)


def clock_synced() -> bool:
    try:
        out = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return out == "yes"
    except Exception:
        return False


def git_head() -> str:
    return subprocess.run(
        ["git", "-C", REPO_DIR, "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def git_pull() -> bool:
    """Pull; return True if HEAD changed."""
    before = git_head()
    result = subprocess.run(
        ["git", "-C", REPO_DIR, "pull", "--ff-only"],
        capture_output=True, text=True, timeout=180,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode != 0:
        logger.warning("git pull failed: %s", result.stderr.strip())
        return False
    changed = git_head() != before
    if changed:
        logger.info("new code pulled: %s", git_head()[:8])
    return changed


def update_panel(st: dict, battery: float | None, force: str | None = None) -> None:
    """Fetch and flash if the value changed (or `force` names a reason to flash
    regardless). Failures are logged, never raised."""
    try:
        data = fetch.fetch_days_since()
    except fetch.FetchError as err:
        logger.warning("fetch failed, leaving panel as-is: %s", err)
        return
    days = data["daysSince"]
    last_event = data.get("lastEvent") or None
    reporter = data.get("reporter")
    # Change-detection keys on what the layout actually shows: the two-panel
    # footer includes the event's time-of-day and the reporter, the single
    # panel only the date.
    if config.PANELS >= 2:
        since_key = (last_event or "")[:16] or None
        reporter_key = reporter
    else:
        since_key = (last_event or "")[:10] or None
        reporter_key = None
    today = date.today().isoformat()
    # One guaranteed flash per day (the 09:00 wake on battery): refreshes the
    # battery % even when nothing changed, and doubles as anti-ghosting
    # maintenance for the panel.
    daily_refresh = st.get("last_flash_date") != today
    if not force and not daily_refresh and days == st.get("last_drawn_value") \
            and since_key == st.get("last_drawn_since") \
            and reporter_key == st.get("last_drawn_reporter") \
            and st.get("last_render_version") == render.RENDER_VERSION:
        logger.info("daysSince=%d unchanged, skipping panel flash", days)
        return
    why = ([", daily refresh"] if daily_refresh else []) + ([f", forced: {force}"] if force else [])
    logger.info("daysSince %s -> %d since %s (render v%d%s), flashing panel",
                st.get("last_drawn_value"), days, since_key, render.RENDER_VERSION, "".join(why))
    try:
        display.flash_value(days, last_event, battery, reporter)
    except Exception as err:
        logger.error("panel flash failed: %s", err)
        return
    st["last_drawn_value"] = days
    st["last_drawn_since"] = since_key
    st["last_drawn_reporter"] = reporter_key
    st["last_render_version"] = render.RENDER_VERSION
    st["last_flash_date"] = today
    state.save(st)


def read_battery() -> float | None:
    try:
        return pisugar.battery_pct()
    except Exception as err:
        logger.warning("battery read failed: %s", err)
        return None


def maybe_daily_pull(st: dict) -> None:
    today = date.today().isoformat()
    if st.get("last_update_date") != today:
        git_pull()  # new code takes effect on the NEXT wake — keeps this wake simple
        st["last_update_date"] = today
        state.save(st)


def field_mode(st: dict, force: str | None = None) -> None:
    # Arm the wake FIRST — everything after this is best-effort. If arming
    # itself fails, still proceed to shutdown: the alarm has a daily repeat,
    # so the previously armed time will wake us; staying up just kills the
    # battery. (Seen in the wild: firmware rejects rtc_alarm_set while
    # auto_power_on is enabled — the two are mutually exclusive.)
    try:
        wake = schedule.next_wake(datetime.now().astimezone())
        pisugar.set_next_alarm(wake)
        st["next_wake"] = wake.isoformat()  # lets the next boot tell alarm from tap
        state.save(st)
    except Exception as err:
        logger.error("failed to arm RTC alarm (%s) — proceeding to shutdown; "
                     "the previously armed daily alarm should still wake us", err)
    battery = read_battery()
    if battery is not None:
        state.log_battery(st, datetime.now().astimezone().isoformat(), battery,
                          pisugar.battery_volts())
        state.save(st)
    maybe_daily_pull(st)
    update_panel(st, battery, force)
    if clock_synced():
        try:
            pisugar.sync_rtc_from_pi()
        except Exception as err:
            logger.warning("RTC sync failed: %s", err)
    # The mode decision was made at boot; if the charger arrived while this
    # cycle ran, shutting down puts a plugged-in device to sleep instead of
    # live-updating. Re-exec so main() re-decides — it will pick watch mode.
    # The already-armed alarm is harmless: it fires into a running Pi.
    try:
        plugged = pisugar.power_plugged()
    except Exception:
        plugged = False
    if plugged:
        logger.info("external power arrived mid-cycle — re-exec into watch mode instead of shutting down")
        reexec()
    shutdown()


pull_poke = threading.Event()  # set by the webhook listener: pull ASAP


def start_webhook_listener() -> None:
    """LAN-only 'pull now' poke, relayed from the GitHub webhook by Mother Brain.

    Unauthenticated by design: it can only trigger a --ff-only pull of the
    public repo, and the port is not forwarded past the LAN.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            pull_poke.set()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")

        def log_message(self, *args):
            pass

    try:
        server = HTTPServer(("0.0.0.0", config.WEBHOOK_PORT), Handler)
    except OSError as err:
        logger.warning("webhook listener unavailable: %s", err)
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("webhook listener on :%d", config.WEBHOOK_PORT)


def watch_mode(st: dict, force: str | None = None) -> None:
    logger.info("external power detected — watch mode (interval %ds)", config.WATCH_INTERVAL_SECONDS)
    start_webhook_listener()
    last_pull = 0.0
    last_rtc_sync = 0.0
    while True:
        now = time.monotonic()
        if pull_poke.is_set() or now - last_pull >= config.WATCH_PULL_INTERVAL_SECONDS:
            pull_poke.clear()
            last_pull = now
            if git_pull():
                logger.info("re-exec with new code")
                reexec()
        update_panel(st, read_battery(), force)
        force = None  # only the first pass after a manual start is forced
        if now - last_rtc_sync >= 3600 and clock_synced():
            try:
                pisugar.sync_rtc_from_pi()
                last_rtc_sync = now
            except Exception as err:
                logger.warning("RTC sync failed: %s", err)
        try:
            if not pisugar.power_plugged():
                logger.info("power unplugged — switching to field mode")
                field_mode(st)
                return
        except pisugar.PiSugarError as err:
            logger.warning("power check failed: %s", err)
        # Wake early if the webhook pokes us mid-sleep.
        pull_poke.wait(timeout=config.WATCH_INTERVAL_SECONDS)


def main():
    if os.path.exists(HOLD_FILE):
        logger.warning("%s exists — holding (no panel update, no shutdown)", HOLD_FILE)
        return

    # The Pi has no RTC of its own; until NTP kicks in its clock is whatever
    # fake-hwclock saved. The PiSugar RTC is kept disciplined, so trust it
    # before making any time-based decision.
    try:
        pisugar.sync_pi_from_rtc()
    except Exception as err:
        logger.warning("could not set Pi clock from PiSugar RTC: %s", err)

    st = state.load()
    now = datetime.now().astimezone()
    reason = wake_reason(st, now)
    # Single tap on battery / double tap while plugged = "redraw now", even if
    # nothing changed. Alarm wakes and re-execs keep the change-only rule.
    force = reason if reason in ("manual", "restart") else None
    if reason != "reexec":
        st["last_wake_reason"] = reason
        st["last_wake_at"] = now.isoformat()
        state.save(st)
    logger.info("wake reason: %s%s", reason, " — forcing a panel redraw" if force else "")

    try:
        plugged = pisugar.power_plugged()
    except Exception as err:
        # Can't tell — assume battery so we never strand the device awake.
        logger.error("power_plugged check failed (%s), assuming battery", err)
        plugged = False

    if plugged:
        watch_mode(st, force)
    else:
        field_mode(st, force)


if __name__ == "__main__":
    main()
