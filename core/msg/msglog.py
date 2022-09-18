import logging
import time
import typing
import aiofiles
from core.util import funcutil
from core.msg import msgabc, msgftr, msgtrf


class LoggingPublisher:
    CRITICAL = 'LoggingPublisher.CRITICAL'
    ERROR = 'LoggingPublisher.ERROR'
    WARNING = 'LoggingPublisher.WARNING'
    INFO = 'LoggingPublisher.INFO'
    DEBUG = 'LoggingPublisher.DEBUG'
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
        super().__init__(msgftr.Or(msg_filter, msgftr.IsStop()))
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
