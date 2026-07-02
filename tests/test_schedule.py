"""Unit tests for the wake schedule policy. Run: python3 -m unittest discover tests"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from dayssince.schedule import next_wake

TZ = timezone(timedelta(hours=-4))


def dt(h, m, s=0):
    return datetime(2026, 7, 1, h, m, s, tzinfo=TZ)


class NextWakeTests(unittest.TestCase):
    def test_midday_goes_to_next_quarter(self):
        self.assertEqual(next_wake(dt(10, 3)), dt(10, 15))

    def test_wall_clock_aligned_not_boot_relative(self):
        # 10:07:30 + 15min would be 10:22:30; slots must land on :00/:15/:30/:45
        self.assertEqual(next_wake(dt(10, 7, 30)), dt(10, 15))

    def test_exact_slot_boundary_advances(self):
        # Waking AT 10:15, the next wake is 10:30 (margin pushes past 10:15)
        self.assertEqual(next_wake(dt(10, 15)), dt(10, 30))

    def test_margin_skips_imminent_slot(self):
        # 90s margin: at 10:14:00 the 10:15 slot is only 60s away -> skip to 10:30
        self.assertEqual(next_wake(dt(10, 14)), dt(10, 30))
        # at 10:13:00 the 10:15 slot is 120s away -> still fine
        self.assertEqual(next_wake(dt(10, 13)), dt(10, 15))

    def test_before_window_waits_for_start(self):
        self.assertEqual(next_wake(dt(7, 42)), dt(9, 0))

    def test_late_afternoon_rolls_to_next_morning(self):
        self.assertEqual(next_wake(dt(16, 46)), dt(17, 0))
        self.assertEqual(next_wake(dt(17, 0)), dt(9, 0) + timedelta(days=1))
        self.assertEqual(next_wake(dt(23, 30)), dt(9, 0) + timedelta(days=1))

    def test_just_after_midnight(self):
        self.assertEqual(next_wake(dt(0, 10)), dt(9, 0))

    def test_result_is_always_in_the_future(self):
        now = dt(8, 59, 59)
        self.assertGreater(next_wake(now), now)


if __name__ == "__main__":
    unittest.main()
