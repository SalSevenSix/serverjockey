import unittest
from core.util import io


class TestCoreUtilIo(unittest.IsolatedAsyncioTestCase):

    async def test_find_files(self):
        result = await io.find_files('test', 'io.py')
        self.assertEqual(1, len(result))
        self.assertEqual('test/unit/core/util/io.py', result[0])
