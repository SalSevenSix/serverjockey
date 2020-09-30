import asyncio
import logging
import uuid
import collections
import typing
from core import msgabc, msgftr, msgtrf, aggtrf, tasks, util


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
        await self._task   # TODO Add timeout then cancel task

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
        return response.get_data()

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
                 transformer: msgabc.Transformer = msgtrf.ToString(),
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
                 transformer: msgabc.Transformer = msgtrf.ToString(),
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
