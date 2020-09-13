import asyncio
import logging
import uuid
import collections
from core import msgsvc, msgftr, msgtrf


class SynchronousMessenger:

    def __init__(self, mailer):
        self.mailer = mailer
        self.catcher = None
        self.timeout = None

    def with_catcher(self, catcher):
        self.catcher = catcher
        return self

    def with_timeout(self, timeout):
        self.timeout = timeout
        return self

    async def request(self, message):
        assert not (self.catcher and self.timeout)
        catcher = self.catcher if self.catcher else SingleCatcher(msgftr.ReplyToIs(message), self.timeout)
        self.mailer.register(catcher)
        self.mailer.post(message)
        return await catcher.get()


class MultiCatcher:

    def __init__(self, catch_filter,
                 stop_filter, include_stop=False,
                 start_filter=None, include_start=False,
                 stop_only_after_start=False,
                 timeout=None):
        self.catch_filter = catch_filter
        self.timeout = timeout
        self.stop_filter = stop_filter
        self.include_stop = include_stop
        self.queue = asyncio.Queue(maxsize=1)
        self.collector = []
        self.start_filter = start_filter
        self.include_start = include_start
        self.stop_only_after_start = stop_only_after_start
        self.started = False
        self.expired = False
        if not start_filter:
            self.start_filter = msgftr.AcceptNothing()
            self.stop_only_after_start = False
            self.started = True

    async def get(self):
        try:
            result = await asyncio.wait_for(self.queue.get(), self.timeout)
            self.queue.task_done()
            return result
        finally:
            self.expired = True

    def accepts(self, message):
        return self.expired \
            or self.catch_filter.accepts(message) \
            or self.stop_filter.accepts(message) \
            or self.start_filter.accepts(message)

    def handle(self, message):
        if self.expired:
            return False
        starting = not self.started and self.start_filter.accepts(message)
        stopping = self.stop_filter.accepts(message)
        if self.stop_only_after_start and stopping and not self.started and not starting:
            return None
        if starting and stopping:
            stopping = False
        if starting:
            self.started = True
        if not self.started:
            return None
        if starting or stopping:
            if starting and self.include_start:
                self.collector.append(message)
            elif stopping and self.include_stop:
                self.collector.append(message)
        else:
            self.collector.append(message)
        if stopping:
            result = tuple(self.collector)
            self.queue.put_nowait(result)
            return result
        return None


class SingleCatcher:

    def __init__(self, msg_filter, timeout=None):
        self.catcher = MultiCatcher(msg_filter, msg_filter, include_stop=True, timeout=timeout)

    async def get(self):
        result = await self.catcher.get()
        return None if len(result) == 0 else result[0]

    def accepts(self, message):
        return self.catcher.accepts(message)

    def handle(self, message):
        result = self.catcher.handle(message)
        if result is None:
            return None
        return None if len(result) == 0 else result[0]


class Publisher:
    START = 'Publisher.Start'
    END = 'Publisher.End'

    def __init__(self, mailer, producer):
        assert msgsvc.is_multimailer(mailer)
        self.mailer = mailer
        self.producer = producer
        self.task = asyncio.create_task(self.run())
        self.mailer.post((self, Publisher.START, producer))

    async def stop(self):
        await self.task

    async def run(self):
        running = True
        while running:
            message = None
            try:
                message = await self.producer.next_message()
            except Exception as e:
                logging.error('Publishing exception. raised: %s', e)
            running = False if message is None else self.mailer.post(message)
        self.mailer.post((self, Publisher.END, self.producer))


class SleepPoster:

    def __init__(self, mailer):
        assert msgsvc.is_multimailer(mailer)
        self.mailer = mailer

    def post(self, message, delay):
        asyncio.create_task(self._post(message, delay))

    async def _post(self, message, delay):
        await asyncio.sleep(delay)
        self.mailer.post(message)


class RollingLogSubscriber:
    INIT = 'RollingLogSubscriber.Init'
    REQUEST = 'RollingLogSubscriber.Request'
    RESPONSE = 'RollingLogSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)

    def __init__(self, mailer,
                 transformer=msgtrf.Noop(),
                 msg_filter=msgftr.AcceptAll(),
                 size=20, identity=None):
        assert msgsvc.is_multimailer(mailer)
        self.mailer = mailer
        self.identity = identity if identity is not None else str(uuid.uuid4())
        self.transformer = transformer
        self.request_filter = msgftr.And((
            RollingLogSubscriber.REQUEST_FILTER,
            msgftr.DataEquals(self.identity)
        ))
        self.msg_filter = msgftr.Or((msg_filter, self.request_filter))
        self.size = size
        self.container = collections.deque()
        mailer.post((self, RollingLogSubscriber.INIT, self.identity))

    @staticmethod
    async def request(mailer, source, identity):
        messenger = SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, RollingLogSubscriber.REQUEST, identity))
        return response.get_data()

    def get_identity(self):
        return self.identity

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    def handle(self, message):
        if self.request_filter.accepts(message):
            self.mailer.post((self, RollingLogSubscriber.RESPONSE, tuple(self.container), message))
        else:
            self.container.append(self.transformer.transform(message))
            while len(self.container) > self.size:
                self.container.popleft()
        return None


class LoggerSubscriber:

    def __init__(self, level=logging.DEBUG, transformer=msgtrf.ToString(), msg_filter=msgftr.AcceptAll()):
        self.level = level
        self.transformer = transformer
        self.msg_filter = msg_filter

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    def handle(self, message):
        logging.log(self.level, self.transformer.transform(message))
        return None


class PrintSubscriber:

    def __init__(self, transformer=msgtrf.ToString(), msg_filter=msgftr.AcceptAll()):
        self.transformer = transformer
        self.msg_filter = msg_filter

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    def handle(self, message):
        print(self.transformer.transform(message))
        return None
