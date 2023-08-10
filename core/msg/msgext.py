import asyncio
import enum
import logging
import collections
import typing
# ALLOW util.* msg.*
from core.util import aggtrf, tasks, util, io, pack, funcutil, objconv
from core.msg import msgabc, msgftr, msgtrf, msglog


class SynchronousMessenger:

    def __init__(self, mailer: msgabc.MulticastMailer,
                 timeout: typing.Optional[float] = None,
                 catcher: typing.Optional[msgabc.Catcher] = None):
        assert not (timeout and catcher)
        self._mailer = mailer
        self._timeout = timeout
        self._catcher = catcher

    async def request(self, *vargs) -> typing.Union[None, msgabc.Message, typing.Collection[msgabc.Message]]:
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
            util.clear_queue(self._queue)
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
        result = self._catcher.handle(message)
        if isinstance(result, tuple):
            return util.single(result)
        return result


class Publisher:
    START, END = 'Publisher.Start', 'Publisher.End'

    def __init__(self, mailer: msgabc.Mailer, producer: msgabc.Producer):
        self._mailer = mailer
        self._producer = producer
        self._task = tasks.task_start(self._run(), name=objconv.obj_to_str(producer))
        self._mailer.post(self, Publisher.START, producer)

    async def stop(self):
        await tasks.wait_for(self._task, 3.0)

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


class SyncReply(enum.Enum):
    AT_START = enum.auto(),
    AT_END = enum.auto(),
    NEVER = enum.auto()


class SyncWrapper(msgabc.AbcSubscriber):
    START, END = 'SyncWrapper.Start', 'SyncWrapper.End'

    def __init__(self,
                 mailer: msgabc.Mailer,
                 delegate: msgabc.Subscriber,
                 reply: SyncReply = SyncReply.NEVER):
        super().__init__(delegate)
        self._mailer = mailer
        self._delegate = delegate
        self._reply = reply

    async def handle(self, message):
        source = message.source()
        self._mailer.post(source, SyncWrapper.START, True,
                          message if self._reply is SyncReply.AT_START else None)
        result = await msgabc.try_handle(self._delegate, message)
        self._mailer.post(source, SyncWrapper.END, True if result is None else result,
                          message if self._reply is SyncReply.AT_END else None)
        return result


class Archiver(msgabc.AbcSubscriber):
    REQUEST = 'Archiver.Request'
    START, COMPLETE, EXCEPTION = 'Archiver.Start', 'Archiver.Complete', 'Archiver.Exception'
    FILTER_START, FILTER_DONE = msgftr.NameIs(START), msgftr.NameIn((COMPLETE, EXCEPTION))

    def __init__(self, mailer: msgabc.Mailer, tmp_dir: str = '/tmp'):
        super().__init__(msgftr.NameIs(Archiver.REQUEST))
        self._mailer = mailer
        self._tmp_dir = tmp_dir

    async def handle(self, message):
        source, data = message.source(), message.data()
        try:
            self._mailer.post(source, Archiver.START)
            archive_file = await self._archive(source, data)
            self._mailer.post(source, Archiver.COMPLETE, archive_file, message)
        except Exception as e:
            self._mailer.post(source, Archiver.EXCEPTION, e, message)
        return None

    async def _archive(self, source, data):
        source_dir = util.get('source_dir', data)
        if source_dir is None:
            raise Exception('No source_dir')
        backups_dir = util.get('backups_dir', data)
        if backups_dir is None:
            raise Exception('No backups_dir')
        prune_hours = int(util.get('prunehours', data, 0))
        logger = msglog.LoggingPublisher(self._mailer, source)
        return await pack.archive_directory(source_dir, backups_dir, prune_hours, self._tmp_dir, logger)


class Unpacker(msgabc.AbcSubscriber):
    REQUEST = 'Unpacker.Request'
    START, COMPLETE, EXCEPTION = 'Unpacker.Start', 'Unpacker.Complete', 'Unpacker.Exception'
    FILTER_START, FILTER_DONE = msgftr.NameIs(START), msgftr.NameIn((COMPLETE, EXCEPTION))

    def __init__(self, mailer: msgabc.Mailer, tmp_dir: str = '/tmp'):
        super().__init__(msgftr.NameIs(Unpacker.REQUEST))
        self._mailer = mailer
        self._tmp_dir = tmp_dir

    async def handle(self, message):
        source, data = message.source(), message.data()
        try:
            self._mailer.post(source, Unpacker.START)
            unpack_dir = await self._unpack(source, data)
            self._mailer.post(source, Unpacker.COMPLETE, unpack_dir, message)
        except Exception as e:
            self._mailer.post(source, Unpacker.EXCEPTION, e, message)
        return None

    async def _unpack(self, source, data):
        root_dir = util.get('root_dir', data)
        if root_dir is None or not await io.directory_exists(root_dir):
            raise Exception('No root_dir')
        backups_dir = util.get('backups_dir', data)
        if backups_dir is None or not await io.directory_exists(backups_dir):
            raise Exception('No backups_dir')
        filename = util.get('filename', data)
        if not filename:
            raise Exception('No filename')
        archive = backups_dir + ('' if filename[0] == '/' else '/') + filename
        unpack_dir = root_dir if util.get('to_root', data) else root_dir + '/' + filename.split('/')[-1].split('-')[0]
        wipe = util.get('wipe', data, True)
        logger = msglog.LoggingPublisher(self._mailer, source)
        await pack.unpack_directory(archive, unpack_dir, wipe, self._tmp_dir, logger)
        return unpack_dir


class RelaySubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        super().__init__(msg_filter)
        self._mailer = mailer

    def handle(self, message):
        return None if self._mailer.post(message) else True


class RollingLogSubscriber(msgabc.Subscriber):
    REQUEST = 'RollingLogSubscriber.Request'
    RESPONSE = 'RollingLogSubscriber.Response'

    def __init__(self, mailer: msgabc.Mailer, size: int = 20,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.Noop(),
                 aggregator: aggtrf.Aggregator = aggtrf.Noop()):
        self._mailer = mailer
        self._size = size
        self._transformer = transformer
        self._aggregator = aggregator
        self._identity = util.generate_id()
        self._request_filter = msgftr.And(
            msgftr.NameIs(RollingLogSubscriber.REQUEST),
            msgftr.DataEquals(self._identity))
        self._msg_filter = msgftr.Or(msg_filter, self._request_filter)
        self._container = collections.deque()

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any, identity: str) -> typing.Any:
        messenger = SynchronousMessenger(mailer)
        response = await messenger.request(source, RollingLogSubscriber.REQUEST, identity)
        return response.data()

    def identity(self) -> str:
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


class CallableSubscriber(msgabc.AbcSubscriber):

    def __init__(self, msg_filter: msgabc.Filter, callback: typing.Callable):
        super().__init__(msg_filter)
        self._callback = callback

    async def handle(self, message):
        await funcutil.silently_call(self._callback)
        return None
