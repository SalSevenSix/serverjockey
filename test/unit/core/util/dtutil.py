import unittest
from core.util import dtutil

_TIMESTAMP = 1738910489.8691483
_DURATION = 60.0 * 60.0 * 24.0 + 60.0 * 60.0 * 2.0 + 60.0 * 3.0 + 4


class TestCoreUtilDtutil(unittest.TestCase):

    def test_format_time_standard(self):
        self.assertEqual('2025-02-07 13:41:29', dtutil.format_time_standard(_TIMESTAMP))
        self.assertEqual('2025-02-07 13:41:29', dtutil.format_time_standard(_TIMESTAMP, True))
        self.assertEqual('2025-02-07 06:41:29', dtutil.format_time_standard(_TIMESTAMP, False))

    def test_format_timezone_standard(self):
        self.assertEqual('+00:00', dtutil.format_timezone_standard(0.0))
        self.assertEqual('+07:00', dtutil.format_timezone_standard(7.0 * 60.0 * 60.0))
        self.assertEqual('+11:30', dtutil.format_timezone_standard(11.0 * 60.0 * 60.0 + 30.0 * 60.0))
        self.assertEqual('-07:00', dtutil.format_timezone_standard(-7.0 * 60.0 * 60.0))
        self.assertEqual('-11:30', dtutil.format_timezone_standard(-11.0 * 60.0 * 60.0 + -30.0 * 60.0))

    def test_duration_to_dict(self):
        self.assertEqual("{'d': 1, 'h': 2, 'm': 3, 's': 4}",
                         str(dtutil.duration_to_dict(_DURATION, parts='dhms')))
        self.assertEqual("{'d': -1, 'h': -2, 'm': -3, 's': -4}",
                         str(dtutil.duration_to_dict(0 - _DURATION, parts='dhms')))

    def test_duration_to_str(self):
        self.assertEqual('0d 0h 0m', dtutil.duration_to_str(0.0))
        self.assertEqual('0d 0h 1m', dtutil.duration_to_str(60.0))
        self.assertEqual('0d 1h 0m', dtutil.duration_to_str(60.0 * 60.0))
        self.assertEqual('1d 0h 0m', dtutil.duration_to_str(60.0 * 60.0 * 24.0))
        self.assertEqual('24h 0m', dtutil.duration_to_str(60.0 * 60.0 * 24.0, parts='hm'))
        self.assertEqual('30m 12s', dtutil.duration_to_str(60.0 * 30.0 + 12.9, parts='ms'))
        self.assertEqual('1d 2h 3m 4s', dtutil.duration_to_str(_DURATION, parts='dhms'))
        self.assertEqual('-1d -2h -3m -4s', dtutil.duration_to_str(-1 * _DURATION, parts='dhms'))
