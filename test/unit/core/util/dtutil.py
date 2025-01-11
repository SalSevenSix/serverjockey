import unittest
from core.util import dtutil


class TestCoreUtilDtutil(unittest.TestCase):

    def test_human_duration(self):
        self.assertEqual('0d 0h 0m', dtutil.human_duration(0.0))
        self.assertEqual('0d 0h 1m', dtutil.human_duration(60.0))
        self.assertEqual('0d 1h 0m', dtutil.human_duration(60.0 * 60.0))
        self.assertEqual('1d 0h 0m', dtutil.human_duration(60.0 * 60.0 * 24.0))
        self.assertEqual('24h 0m', dtutil.human_duration(60.0 * 60.0 * 24.0, parts=2))
