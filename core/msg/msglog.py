import logging
import time
import typing
import aiofiles
# ALLOW util.* msg.msgabc msg.msgftr msg.msgtrf
from core.util import util, io, funcutil
from core.msg import msgabc, msgftr, msgtrf

CRITICAL = 'MessageLogging.CRITICAL'
ERROR = 'MessageLogging.ERROR'
WARNING = 'MessageLogging.WARNING'
INFO = 'MessageLogging.INFO'
DEBUG = 'MessageLogging.DEBUG'
FILTER_ALL_LEVELS = msgftr.NameIn((DEBUG, INFO, WARNING, ERROR, CRITICAL))


class LoggingPublisher:
    _LEVEL_MAP = {
        logging.CRITICAL: CRITICAL,
        logging.ERROR: ERROR,
        logging.WARNING: WARNING,
        logging.INFO: INFO,
        logging.DEBUG: DEBUG
    }

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any):
        self._mailer = mailer
        self._source = source

    # noinspection PyUnusedLocal
    def log(self, level, msg, *args, **kwargs):
        self._mailer.post(self._source, LoggingPublisher._LEVEL_MAP[level], msg % args)

    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        self.critical(msg, *args, **kwargs)


class LogfileSubscriber(msgabc.AbcSubscriber):

    def __init__(self,
                 filename: str,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 roll_filter: msgabc.Filter = msgftr.AcceptNothing(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msgftr.Or(msg_filter, roll_filter, msgftr.IsStop()))
        self._roll_filter = roll_filter
        self._transformer = transformer
        self._filename = filename
        self._file = None

    async def handle(self, message):
        if message is msgabc.STOP:
            await funcutil.silently_cleanup(self._file)
            return True
        if self._roll_filter.accepts(message):
            await funcutil.silently_cleanup(self._file)
            self._file = None
            return None
        try:
            if self._file is None:
                filename = time.strftime(self._filename, time.localtime(time.time()))
                self._file = await aiofiles.open(filename, mode='w')
            await self._file.write(self._transformer.transform(message))
            await self._file.write('\n')
            await self._file.flush()
        except Exception as e:
            await funcutil.silently_cleanup(self._file)
            logging.error('LogfileSubscriber raised: %s', repr(e))
            return False
        return None


class LoggerSubscriber(msgabc.AbcSubscriber):

    def __init__(self,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 level: int = logging.DEBUG,
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msg_filter)
        self._level = level
        self._transformer = transformer

    def handle(self, message):
        logging.log(self._level, self._transformer.transform(message))
        return None


class PrintSubscriber(msgabc.AbcSubscriber):

    def __init__(self,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msg_filter)
        self._transformer = transformer

    def handle(self, message):
        print(self._transformer.transform(message))
        return None


class PercentTracker(io.BytesTracker):

    def __init__(self, mailer: msgabc.Mailer, expected: int, notifications: int = 10,
                 prefix: str = 'progress', msg_name: str = INFO):
        self._mailer = mailer
        self._msg_name = msg_name
        self._expected = expected
        self._prefix = prefix
        self._increment = int(expected / notifications)
        self._bytes, self._next_target = _Bytes(), self._increment

    def processed(self, chunk: bytes | None):
        if chunk is None:
            self._bytes, self._next_target = _Bytes(), self._increment
            return
        total = self._bytes.add(chunk)
        if total >= self._expected:
            message = self._prefix + ' 100% (' + self._bytes.rate() + ')'
            self._mailer.post(self, self._msg_name, message)
        elif total > self._next_target:
            self._next_target += self._increment
            percentage = str(int((total / self._expected) * 100.0))
            message = self._prefix + '  ' + percentage + '% (' + self._bytes.rate() + ')'
            self._mailer.post(self, self._msg_name, message)


class IntervalTracker(io.BytesTracker):

    def __init__(self, mailer: msgabc.Mailer, interval: float = 1.0, msg_name: str = INFO,
                 initial_message: str = 'RECEIVING data...', prefix: str = 'received'):
        self._mailer = mailer
        self._msg_name = msg_name
        self._initial_message = initial_message
        self._interval = interval
        self._prefix = prefix
        self._bytes, self._last_time = _Bytes(), 0

    def processed(self, chunk: bytes | None):
        if chunk is None:
            message = self._prefix + ' ' + util.human_file_size(self._bytes.total())
            message += ' Total (' + self._bytes.rate() + ')'
            self._mailer.post(self, self._msg_name, message)
            self._bytes, self._last_time = _Bytes(), 0
            return
        if not self._last_time:
            self._last_time = time.time()
            if self._initial_message:
                self._mailer.post(self, self._msg_name, self._initial_message)
        self._bytes.add(chunk)
        now = time.time()
        if now - self._last_time > self._interval:
            message = self._prefix + ' ' + util.human_file_size(self._bytes.total())
            message += ' (' + self._bytes.rate() + ')'
            self._mailer.post(self, self._msg_name, message)
            self._last_time = now


class _Bytes:

    def __init__(self):
        self._start_time = 0
        self._total = 0

    def add(self, chunk: bytes) -> int:
        if not self._start_time:
            self._start_time = time.time()
        self._total += len(chunk)
        return self._total

    def total(self) -> int:
        return self._total

    def rate(self) -> str:
        return util.human_file_size(int(self._total / (time.time() - self._start_time))) + '/s'
