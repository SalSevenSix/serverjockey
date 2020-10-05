import asyncio
import enum
import logging
import time
import uuid
import collections
import typing
from core.util import aggtrf, tasks, util
from core.msg import msgabc, msgftr, msgtrf


class SynchronousMessenger:

    def __init__(self, mailer: msgabc.MulticastMailer,
                 timeout: typing.Optional[float] = None,
                 catcher: typing.Optional[msgabc.Catcher] = None):
        self._mailer = mailer
        self._timeout = timeout
        self._catcher = catcher

    async def request(self, *vargs) -> typing.Union[None, msgabc.Message, typing.Collection[msgabc.Message]]:
        assert not (self._catcher and self._timeout)
        message = msgabc.Message.from_vargs(*vargs)
        catcher = self._catcher if self._catcher else SingleCatcher(msgftr.ReplyToIs(message), self._timeout)
        self._mailer.register(catcher)
        self._mailer.post(message)
        return await catcher.get()


class MultiCatcher(msgabc.Catcher):

    def __init__(self,
                 catch_filter: msgabc.Filter,
                 stop_filter: msgabc.Filter,
                 include_stop: bool = False,
                 start_filter: typing.Optional[msgabc.Filter] = None,
                 include_start: bool = False,
                 stop_only_after_start: bool = False,
                 timeout: typing.Optional[float] = None):
        self._catch_filter = catch_filter
        self._timeout = timeout
        self._stop_filter = stop_filter
        self._include_stop = include_stop
        self._queue = asyncio.Queue(maxsize=1)
        self._collector = []
        self._start_filter = start_filter
        self._include_start = include_start
        self._stop_only_after_start = stop_only_after_start
        self._started = False
        self._expired = False
        if not start_filter:
            self._start_filter = msgftr.AcceptNothing()
            self._stop_only_after_start = False
            self._started = True

    async def get(self) -> typing.Collection[msgabc.Message]:
        try:
            messages = await asyncio.wait_for(self._queue.get(), self._timeout)
            self._queue.task_done()
            return messages
        finally:
            self._expired = True

    def accepts(self, message):
        return self._expired \
            or self._catch_filter.accepts(message) \
            or self._stop_filter.accepts(message) \
            or self._start_filter.accepts(message)

    def handle(self, message):
        if self._expired:
            return False
        starting = not self._started and self._start_filter.accepts(message)
        stopping = self._stop_filter.accepts(message)
        if self._stop_only_after_start and stopping and not self._started and not starting:
            return None
        if starting and stopping:
            stopping = False
        if starting:
            self._started = True
        if not self._started:
            return None
        if starting or stopping:
            if starting and self._include_start:
                self._collector.append(message)
            elif stopping and self._include_stop:
                self._collector.append(message)
        else:
            self._collector.append(message)
        if stopping:
            messages = tuple(self._collector)
            self._queue.put_nowait(messages)
            return messages
        return None


class SingleCatcher(msgabc.Catcher):

    def __init__(self, msg_filter: msgabc.Filter, timeout: typing.Optional[float] = None):
        self._catcher = MultiCatcher(msg_filter, msg_filter, include_stop=True, timeout=timeout)

    async def get(self) -> typing.Optional[msgabc.Message]:
        messages = await self._catcher.get()
        return util.single(messages)

    def accepts(self, message):
        return self._catcher.accepts(message)

    def handle(self, message):
        messages = self._catcher.handle(message)
        if not isinstance(messages, tuple):
            return messages
        return util.single(messages)


class Publisher:
    START = 'Publisher.Start'
    END = 'Publisher.End'

    def __init__(self, mailer: msgabc.Mailer, producer: msgabc.Producer):
        self._mailer = mailer
        self._producer = producer
        self._task = tasks.task_start(self._run(), name=util.obj_to_str(producer))
        self._mailer.post(self, Publisher.START, producer)

    async def stop(self):
        try:
            await asyncio.wait_for(self._task, 3.0)
        except asyncio.TimeoutError:
            self._task.cancel()

    async def _run(self):
        running = True
        while running:
            message = None
            try:
                message = await self._producer.next_message()
            except Exception as e:
                logging.error('Publishing exception. raised: %s', e)
            running = False if message is None else self._mailer.post(message)
        self._mailer.post(self, Publisher.END, self._producer)
        tasks.task_end(self._task)


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


class SetSubscriber(msgabc.Subscriber):

    def __init__(self, *delegates: msgabc.Subscriber):
        self._delegates = list(delegates)

    def accepts(self, message):
        for delegate in iter(self._delegates):
            if delegate.accepts(message):
                return True
        return False

    async def handle(self, message):
        expired = []
        for delegate in iter(self._delegates):
            if delegate.accepts(message):
                result = await msgabc.try_handle('SetSubscriber', delegate, message)
                if result is not None:
                    expired.append(delegate)
        for delegate in iter(expired):
            self._delegates.remove(delegate)
        if len(self._delegates) == 0 or message is msgabc.STOP:
            return True
        return None


class MonitorReply(enum.Enum):
    AT_START = enum.auto(),
    AT_END = enum.auto(),
    NEVER = enum.auto()


class MonitorSubscriber(msgabc.Subscriber):
    START = 'MonitorSubscriber.Start'
    END = 'MonitorSubscriber.End'

    def __init__(self,
                 mailer: msgabc.Mailer,
                 delegate: msgabc.Subscriber,
                 reply: MonitorReply = MonitorReply.NEVER):
        self._mailer = mailer
        self._delegate = delegate
        self._reply = reply

    def accepts(self, message):
        return self._delegate.accepts(message)

    async def handle(self, message):
        source = message.source()
        self._mailer.post(source, MonitorSubscriber.START, self._delegate,
                          message if self._reply is MonitorReply.AT_START else None)
        result = await msgabc.try_handle('MonitorSubscriber', self._delegate, message)
        self._mailer.post(source, MonitorSubscriber.END, result,
                          message if self._reply is MonitorReply.AT_END else None)
        return result


class TimeoutSubscriber(msgabc.Subscriber):
    EXCEPTION = 'TimeoutSubscriber.Exception'

    def __init__(self, mailer: msgabc.Mailer, delegate: msgabc.Subscriber, timeout: float = 1.0):
        self._mailer = mailer
        self._delegate = delegate
        self._timeout = timeout
        self._queue = asyncio.Queue(maxsize=2)
        self._task = tasks.task_start(self._run(), name=util.obj_to_str(self))
        self._running = True

    def accepts(self, message):
        return self._delegate.accepts(message) or message is msgabc.STOP

    async def handle(self, message):
        if message is msgabc.STOP:
            self._running = False
            self._queue.put_nowait(msgabc.STOP)
            return True
        source = message.source()
        timeout = self._timeout - (time.time() - message.created())
        if timeout < 0.0:
            self._mailer.post(source, TimeoutSubscriber.EXCEPTION, Exception('Timeout in mailer queue'), message)
            return None if self._running else True
        try:
            await asyncio.wait_for(self._queue.join(), timeout)
            if self._running:
                self._queue.put_nowait(message)
            else:
                self._mailer.post(source, TimeoutSubscriber.EXCEPTION, Exception('Job task has ended'), message)
        except asyncio.TimeoutError:
            self._mailer.post(source, TimeoutSubscriber.EXCEPTION, Exception('Timeout in job queue'), message)
        return None if self._running else True

    async def _run(self):
        while self._running:
            message = await self._queue.get()
            if self._running:
                result = await msgabc.try_handle('TimeoutSubscriber', self._delegate, message)
                self._running = self._running and result is None
                self._queue.task_done()
        tasks.task_end(self._task)


class RelaySubscriber(msgabc.Subscriber):

    def __init__(self, mailer: msgabc.Mailer, msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        self._mailer = mailer
        self._msg_filter = msg_filter

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    def handle(self, message):
        return None if self._mailer.post(message) else True


class RollingLogSubscriber(msgabc.Subscriber):
    INIT = 'RollingLogSubscriber.Init'
    REQUEST = 'RollingLogSubscriber.Request'
    RESPONSE = 'RollingLogSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)

    def __init__(self, mailer: msgabc.Mailer,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.Noop(),
                 aggregator: aggtrf.Aggregator = aggtrf.Noop(),
                 size: int = 20,
                 identity: typing.Optional[str] = None):
        self._mailer = mailer
        self._identity = identity if identity else str(uuid.uuid4())
        self._transformer = transformer
        self._aggregator = aggregator
        self._request_filter = msgftr.And(
            RollingLogSubscriber.REQUEST_FILTER,
            msgftr.DataEquals(self._identity))
        self._msg_filter = msgftr.Or(msg_filter, self._request_filter)
        self._size = size
        self._container = collections.deque()
        mailer.post(self, RollingLogSubscriber.INIT, self._identity)

    @staticmethod
    async def get_log(mailer: msgabc.MulticastMailer, source: typing.Any, identity: str) -> typing.Any:
        messenger = SynchronousMessenger(mailer)
        response = await messenger.request(source, RollingLogSubscriber.REQUEST, identity)
        return response.data()

    def get_identity(self) -> str:
        return self._identity

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    def handle(self, message):
        if self._request_filter.accepts(message):
            result = self._aggregator.aggregate(tuple(self._container))
            self._mailer.post(self, RollingLogSubscriber.RESPONSE, result, message)
        else:
            self._container.append(self._transformer.transform(message))
            while len(self._container) > self._size:
                self._container.popleft()
        return None


class LoggerSubscriber(msgabc.Subscriber):

    def __init__(self,
                 level: int = logging.DEBUG,
                 transformer: msgabc.Transformer = msgtrf.ToLogLine(),
                 msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        self._level = level
        self._transformer = transformer
        self._msg_filter = msg_filter

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    def handle(self, message):
        logging.log(self._level, self._transformer.transform(message))
        return None


class PrintSubscriber(msgabc.Subscriber):

    def __init__(self,
                 transformer: msgabc.Transformer = msgtrf.ToLogLine(),
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 file: typing.Optional[str] = None,
                 flush: bool = False):
        self._transformer = transformer
        self._msg_filter = msg_filter
        self._file = file
        self._flush = flush

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    def handle(self, message):
        print(self._transformer.transform(message), file=self._file, flush=self._flush)
        return None
