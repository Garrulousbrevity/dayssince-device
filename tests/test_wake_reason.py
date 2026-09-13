"""Unit tests for alarm-vs-manual wake attribution. Run: python3 -m unittest discover tests"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from dayssince.schedule import is_alarm_wake

TZ = timezone(timedelta(hours=-4))
ARMED = datetime(2026, 9, 14, 9, 0, tzinfo=TZ)


def boot(**kw):
    return ARMED + timedelta(**kw)


class IsAlarmWakeTests(unittest.TestCase):
    def test_boot_shortly_after_armed_time_is_alarm(self):
        self.assertTrue(is_alarm_wake(boot(seconds=45), ARMED.isoformat()))
        self.assertTrue(is_alarm_wake(boot(minutes=3, seconds=59), ARMED.isoformat()))

    def test_boot_well_after_window_is_manual(self):
        self.assertFalse(is_alarm_wake(boot(minutes=7), ARMED.isoformat()))

    def test_boot_before_armed_time_is_manual(self):
        # An alarm can't boot us before it fires (beyond a little clock slop).
        self.assertFalse(is_alarm_wake(boot(minutes=-5), ARMED.isoformat()))
        self.assertTrue(is_alarm_wake(boot(seconds=-30), ARMED.isoformat()))

    def test_same_time_of_day_on_a_later_day_is_alarm(self):
        # Re-arming failed: the old time-of-day still fires daily.
        self.assertTrue(is_alarm_wake(boot(days=1, seconds=50), ARMED.isoformat()))
        self.assertTrue(is_alarm_wake(boot(days=3, seconds=50), ARMED.isoformat()))

    def test_no_record_or_garbage_is_manual(self):
        self.assertFalse(is_alarm_wake(boot(seconds=30), None))
        self.assertFalse(is_alarm_wake(boot(seconds=30), ""))
        self.assertFalse(is_alarm_wake(boot(seconds=30), "not-a-date"))
        # naive vs aware can't be compared — treat as unknown, i.e. manual
        self.assertFalse(is_alarm_wake(boot(seconds=30), "2026-09-14T09:00:00"))

    def test_other_timezone_representation_still_matches(self):
        utc_armed = ARMED.astimezone(timezone.utc).isoformat()
        self.assertTrue(is_alarm_wake(boot(seconds=60), utc_armed))


if __name__ == "__main__":
    unittest.main()
