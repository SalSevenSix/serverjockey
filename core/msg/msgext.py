import asyncio
import enum
import logging
import time
import uuid
import collections
import typing
import aiofiles
from core.util import aggtrf, tasks, util, funcutil, io, pack
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
        result = self._catcher.handle(message)
        if isinstance(result, tuple):
            return util.single(result)
        return result


class Publisher:
    START = 'Publisher.Start'
    END = 'Publisher.End'

    def __init__(self, mailer: msgabc.Mailer, producer: msgabc.Producer):
        self._mailer = mailer
        self._producer = producer
        self._task = tasks.task_start(self._run(), name=util.obj_to_str(producer))
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
        return None if len(self._delegates) > 0 else True


class SyncReply(enum.Enum):
    AT_START = enum.auto(),
    AT_END = enum.auto(),
    NEVER = enum.auto()


class SyncWrapper(msgabc.AbcSubscriber):
    START = 'SyncWrapper.Start'
    END = 'SyncWrapper.End'

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
        result = await msgabc.try_handle('MonitorSubscriber', self._delegate, message)
        self._mailer.post(source, SyncWrapper.END, True if result is None else result,
                          message if self._reply is SyncReply.AT_END else None)
        return result


class TimeoutSubscriber(msgabc.AbcSubscriber):
    EXCEPTION = 'TimeoutSubscriber.Exception'

    def __init__(self, mailer: msgabc.Mailer, delegate: msgabc.Subscriber, timeout: float = 1.0):
        super().__init__(msgftr.Or(delegate, msgftr.IsStop()))
        self._mailer = mailer
        self._delegate = delegate
        self._timeout = timeout
        self._queue = asyncio.Queue(maxsize=2)
        self._task = tasks.task_start(self._run(), name=util.obj_to_str(self))
        self._running = True

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


class ReadWriteFileSubscriber(msgabc.AbcSubscriber):
    READ = 'ReadWriteFileSubscriber.Read'
    WRITE = 'ReadWriteFileSubscriber.Write'
    RESPONSE = 'ReadWriteFileSubscriber.Response'

    @staticmethod
    async def read(mailer: msgabc.MulticastMailer, filename: str) -> str:
        messenger = SynchronousMessenger(mailer)
        response = await messenger.request(
            util.obj_to_str(messenger), ReadWriteFileSubscriber.READ, {'filename': filename})
        return response.data()

    @staticmethod
    async def write(mailer: msgabc.MulticastMailer, filename: str, data: str) -> bool:
        messenger = SynchronousMessenger(mailer)
        response = await messenger.request(
            util.obj_to_str(messenger), ReadWriteFileSubscriber.WRITE, {'filename': filename, 'data': data})
        return response.data()

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.NameIn((ReadWriteFileSubscriber.READ, ReadWriteFileSubscriber.WRITE)))
        self._mailer = mailer

    async def handle(self, message):
        source, name, data = message.source(), message.name(), message.data()
        if name is ReadWriteFileSubscriber.READ:
            file = await io.read_file(data['filename'])
            self._mailer.post(source, ReadWriteFileSubscriber.RESPONSE, file, message)
        if name is ReadWriteFileSubscriber.WRITE:
            await io.write_file(data['filename'], data['data'])
            self._mailer.post(source, ReadWriteFileSubscriber.RESPONSE, True, message)
        return None


class Archiver(msgabc.AbcSubscriber):
    REQUEST = 'Archiver.Request'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.NameIs(Archiver.REQUEST))
        self._mailer = mailer

    async def handle(self, message):
        source_dir = util.get('source_dir', message.data())
        if source_dir is None:
            raise Exception('No source_dir')
        backups_dir = util.get('backups_dir', message.data())
        if backups_dir is None:
            raise Exception('No backups_dir')
        logger = LoggingPublisher(self._mailer, message.source())
        await pack.archive_directory(source_dir, backups_dir, logger)
        return None


class Unpacker(msgabc.AbcSubscriber):
    REQUEST = 'Unpacker.Request'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.NameIs(Unpacker.REQUEST))
        self._mailer = mailer

    async def handle(self, message):
        root_dir = util.get('root_dir', message.data())
        if root_dir is None or not await io.directory_exists(root_dir):
            raise Exception('No root_dir')
        backups_dir = util.get('backups_dir', message.data())
        if backups_dir is None or not await io.directory_exists(backups_dir):
            raise Exception('No backups_dir')
        filename = util.get('filename', message.data())
        if filename is None:
            raise Exception('No filename')
        archive = backups_dir + '/' + filename
        unpack_dir = root_dir + '/' + filename.split('.')[0].split('-')[0]
        logger = LoggingPublisher(self._mailer, message.source())
        await pack.unpack_directory(archive, unpack_dir, logger)
        return None


class RelaySubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer, msg_filter: msgabc.Filter = msgftr.AcceptAll()):
        super().__init__(msg_filter)
        self._mailer = mailer

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


class LogfileSubscriber(msgabc.AbcSubscriber):

    def __init__(self,
                 filename: str,
                 msg_filter: msgabc.Filter = msgftr.AcceptAll(),
                 transformer: msgabc.Transformer = msgtrf.ToLogLine()):
        super().__init__(msgftr.Or(msg_filter, msgftr.IsStop()))
        self._transformer = transformer
        self._filename = filename
        self._file = None

    async def handle(self, message):
        if message is msgabc.STOP:
            await funcutil.silently_cleanup(self._file)
            return True
        try:
            if self._file is None:
                self._file = await aiofiles.open(self._filename, mode='w')
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
