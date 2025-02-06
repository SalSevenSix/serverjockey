import unittest
from core.util import dtutil

_EXAMPLE = 60.0 * 60.0 * 24.0 + 60.0 * 60.0 * 2.0 + 60.0 * 3.0 + 4


class TestCoreUtilDtutil(unittest.TestCase):

    def test_duration_to_dict(self):
        self.assertEqual("{'d': 1, 'h': 2, 'm': 3, 's': 4}", str(dtutil.duration_to_dict(_EXAMPLE, parts='dhms')))

    def test_duration_to_str(self):
        self.assertEqual('0d 0h 0m', dtutil.duration_to_str(0.0))
        self.assertEqual('0d 0h 1m', dtutil.duration_to_str(60.0))
        self.assertEqual('0d 1h 0m', dtutil.duration_to_str(60.0 * 60.0))
        self.assertEqual('1d 0h 0m', dtutil.duration_to_str(60.0 * 60.0 * 24.0))
        self.assertEqual('24h 0m', dtutil.duration_to_str(60.0 * 60.0 * 24.0, parts='hm'))
        self.assertEqual('30m 12s', dtutil.duration_to_str(60.0 * 30.0 + 12.9, parts='ms'))
        self.assertEqual('1d 2h 3m 4s', dtutil.duration_to_str(_EXAMPLE, parts='dhms'))
        self.assertEqual('-1d -2h -3m -4s', dtutil.duration_to_str(-1 * _EXAMPLE, parts='dhms'))
