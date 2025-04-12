import logging
import time
import typing
import aiofiles
# ALLOW util.* msg.msgabc msg.msgftr msg.msgtrf
from core.util import util, dtutil, io, funcutil
from core.msg import msgabc, msgftr, msgtrf


class LogPublisher:
    LOG = 'LogPublisher.Log'
    LOG_FILTER = msgftr.NameIs(LOG)

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any = None, name: str = None):
        self._mailer = mailer
        self._source = source if source else self
        self._name = name if name else LogPublisher.LOG

    def mailer(self):
        return self._mailer

    def source(self):
        return self._source

    def name(self):
        return self._name

    def log(self, msg: str, name: str = None, source: typing.Any = None):
        self._mailer.post(source if source else self._source, name if name else self._name, msg)


class LogfileSubscriber(msgabc.AbcSubscriber):

    def __init__(self, filename: str,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 roll_filter: msgabc.Filter = msgftr.AcceptNothing(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msgftr.Or(msg_filter, roll_filter, msgftr.IsStop()))
        self._filename, self._file = filename, None
        self._roll_filter, self._transformer = roll_filter, transformer

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
                filename = dtutil.format_time(self._filename, message.created())
                self._file = await aiofiles.open(filename, mode='w')
            await self._file.write(self._transformer.transform(message))
            await self._file.write('\n')
            await self._file.flush()
            return None
        except Exception as e:
            await funcutil.silently_cleanup(self._file)
            logging.error('LogfileSubscriber raised: %s', repr(e))
        return False


class LoggerSubscriber(msgabc.AbcSubscriber):

    def __init__(self, msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine(),
                 level: int = logging.DEBUG):
        super().__init__(msg_filter)
        self._transformer, self._level = transformer, level

    def handle(self, message):
        logging.log(self._level, self._transformer.transform(message))
        return None


class PrintSubscriber(msgabc.AbcSubscriber):

    def __init__(self, msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msg_filter)
        self._transformer = transformer

    def handle(self, message):
        print(self._transformer.transform(message))
        return None


class PercentTracker(io.BytesTracker):

    def __init__(self, mailer: msgabc.Mailer, expected: int, notifications: int = 10,
                 prefix: str = 'progress', msg_name: str = LogPublisher.LOG):
        self._mailer, self._expected = mailer, expected
        self._prefix, self._msg_name = prefix, msg_name
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

    def __init__(self, mailer: msgabc.Mailer, interval: float = 1.0, msg_name: str = LogPublisher.LOG,
                 initial_message: str = 'RECEIVING data...', prefix: str = 'received'):
        self._mailer, self._interval, self._msg_name = mailer, interval, msg_name
        self._initial_message, self._prefix = initial_message, prefix
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
        self._start_time, self._total = 0, 0

    def add(self, chunk: bytes) -> int:
        if not self._start_time:
            self._start_time = time.time()
        self._total += len(chunk)
        return self._total

    def total(self) -> int:
        return self._total

    def rate(self) -> str:
        return util.human_file_size(int(self._total / (time.time() - self._start_time))) + '/s'
