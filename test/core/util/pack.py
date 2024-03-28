import unittest
import asyncio
from core.util import pack


class TestCoreUtilPack(unittest.IsolatedAsyncioTestCase):

    async def test_progress_logger(self):
        progress_logger = pack._ProgressLogger(_PrintLogger())
        # progress_logger.start()
        # await asyncio.sleep(380.0)
        progress_logger.stop()


class _PrintLogger:
    def info(self, msg, *args, **kwargs):
        print(msg)
