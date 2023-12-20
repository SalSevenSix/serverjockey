import logging
import asyncio
import typing
import aiofiles
# ALLOW util.* msg.* context.* http.*
from core.util import util, io, tasks, aggtrf, objconv
from core.msg import msgabc, msgext, msgftr, msgtrf, msglog
from core.http import httpabc, httpcnt, httpsubs


class LoginHandler(httpabc.PostHandler):

    def __init__(self, secret: str):
        self._secret = secret

    def handle_post(self, resource, data):
        return self._secret


class MessengerHandler(httpabc.PostHandler):

    def __init__(self,
                 mailer: msgabc.MulticastMailer, name: str,
                 data: typing.Optional[httpabc.ABC_DATA_GET] = None,
                 selector: typing.Optional[httpsubs.Selector] = None):
        self._mailer = mailer
        self._name = name
        self._data = data
        self._selector = selector

    async def handle_post(self, resource, data):
        messenger = msgext.SynchronousMessenger(self._mailer)
        subscription_path, source = None, objconv.obj_to_str(messenger)
        data['resource'] = resource.name()  # TODO I don't think this is ever used
        if self._data:
            data = {**self._data, **data}
        if self._selector:
            subscription_path = await httpsubs.HttpSubscriptionService.subscribe(
                self._mailer, source, httpsubs.Selector(
                    msg_filter=msgftr.And(msgftr.SourceIs(source), self._selector.msg_filter),
                    completed_filter=msgftr.And(msgftr.SourceIs(source), self._selector.completed_filter),
                    transformer=self._selector.transformer, aggregator=self._selector.aggregator))
        response = await messenger.request(source, self._name, data)
        result = response.data()
        if isinstance(result, Exception):
            if subscription_path:
                httpsubs.HttpSubscriptionService.unsubscribe(self._mailer, source, subscription_path)
            return {'error': str(result)}  # TODO probably should just throw error
        if subscription_path:
            return {'url': util.get('baseurl', data, '') + subscription_path}
        if result is False:
            return httpabc.ResponseBody.BAD_REQUEST
        if result is None:
            return httpabc.ResponseBody.NOT_FOUND
        if result is True:
            return httpabc.ResponseBody.NO_CONTENT
        return result


class StaticHandler(httpabc.GetHandler):

    def __init__(self, response: httpabc.ABC_RESPONSE, protected: bool = True):
        self._response, self._protected = response, protected

    def handle_get(self, resource, data):
        if self._protected and not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        return self._response


class ArchiveHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, backups_dir: str, source_dir: str):
        self._handler = MessengerHandler(
            mailer, msgext.Archiver.REQUEST,
            {'backups_dir': backups_dir, 'source_dir': source_dir},
            httpsubs.Selector(
                msg_filter=msglog.FILTER_ALL_LEVELS,
                completed_filter=msgext.Archiver.FILTER_DONE,
                aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class UnpackerHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, backups_dir: str, root_dir: str,
                 to_root: bool = False, wipe: bool = True):
        self._handler = MessengerHandler(
            mailer, msgext.Unpacker.REQUEST,
            {'backups_dir': backups_dir, 'root_dir': root_dir, 'to_root': to_root, 'wipe': wipe},
            httpsubs.Selector(
                msg_filter=msglog.FILTER_ALL_LEVELS,
                completed_filter=msgext.Unpacker.FILTER_DONE,
                aggregator=aggtrf.StrJoin('\n')))

    async def handle_post(self, resource, data):
        return await self._handler.handle_post(resource, data)


class RollingLogHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, msg_filter: msgabc.Filter, size: int = 100):
        self._mailer = mailer
        self._subscriber = msgext.RollingLogSubscriber(
            mailer, size, msg_filter, msgtrf.GetData(), aggtrf.StrJoin('\n'))
        mailer.register(self._subscriber)

    async def handle_get(self, resource, data):
        return await msgext.RollingLogSubscriber.get(self._mailer, self, self._subscriber.identity())


class WipeHandler(httpabc.PostHandler):
    WIPED = 'WipeHandler.Wiped'
    FILTER_DONE = msgftr.NameIs(WIPED)

    def __init__(self, mailer: msgabc.Mailer, path: str):
        self._mailer = mailer
        self._path = path

    async def handle_post(self, resource, data):
        await io.delete_any(self._path)
        self._mailer.post(self, WipeHandler.WIPED, self._path)
        return httpabc.ResponseBody.NO_CONTENT


class FileSystemHandler(httpabc.GetHandler, httpabc.PostHandler):

    def __init__(self, path: str, tail: typing.Optional[str] = None, protected: bool = True,
                 tempdir: str = '/tmp', ls_filter: typing.Callable = None,
                 read_tracker: io.BytesTracker = io.NullBytesTracker(),
                 write_tracker: io.BytesTracker = io.NullBytesTracker()):
        self._path, self._tail, self._protected = path, tail, protected
        self._tempdir, self._ls_filter = tempdir, ls_filter
        self._read_tracker, self._write_tracker = read_tracker, write_tracker

    async def handle_get(self, resource, data):
        if self._protected and not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        path = self._path + '/' + data[self._tail] if self._tail else self._path
        if await io.file_exists(path):
            content_type = httpcnt.ContentTypeImpl.lookup(path)
            size = await io.file_size(path)
            if content_type.is_text_type() and size < 1048576:
                return await io.read_file(path)
            return _FileByteStream(path, self._read_tracker)
        if await io.directory_exists(path):
            result = await io.directory_list(path, data['baseurl'] + resource.path(data))
            return [e for e in result if self._ls_filter(e)] if self._ls_filter else result
        return httpabc.ResponseBody.NOT_FOUND

    async def handle_post(self, resource, data):
        path = self._path + '/' + data[self._tail] if self._tail else self._path
        body = util.get('body', data)
        if not body:
            if await io.file_exists(path):
                await io.delete_file(path)
                return httpabc.ResponseBody.NO_CONTENT
            if await io.directory_exists(path):
                await io.delete_directory(path)
                return httpabc.ResponseBody.NO_CONTENT
            return httpabc.ResponseBody.BAD_REQUEST
        if await io.directory_exists(path):
            return httpabc.ResponseBody.BAD_REQUEST
        if not await io.directory_exists('/'.join(path.split('/')[0:-1])):
            return httpabc.ResponseBody.BAD_REQUEST
        if isinstance(body, str):
            await io.write_file(path, body)
            return httpabc.ResponseBody.NO_CONTENT
        if isinstance(body, httpabc.ByteStream):
            await io.stream_write_file(path, body, tempdir=self._tempdir, tracker=self._write_tracker)
            return httpabc.ResponseBody.NO_CONTENT
        return httpabc.ResponseBody.BAD_REQUEST


class _FileByteStream(httpabc.ByteStream):

    def __init__(self, filename: str, tracker: io.BytesTracker = io.NullBytesTracker()):
        self._name = filename.split('/')[-1]
        self._filename = filename
        self._content_type = httpcnt.ContentTypeImpl.lookup(filename)
        self._queue = asyncio.Queue(maxsize=2)
        self._tracker = tracker
        self._task, self._length = None, -1

    def name(self) -> str:
        return self._name

    def content_type(self) -> httpabc.ContentType:
        return self._content_type

    async def content_length(self) -> int:
        return await io.file_size(self._filename)

    async def read(self, length: int = -1) -> bytes:
        if self._task is None:
            self._length = length
            self._task = tasks.task_start(self._run(), name=self._name)
        try:
            return await asyncio.wait_for(self._queue.get(), 20.0)
        except asyncio.TimeoutError:
            if self._task:
                self._task.cancel()
            raise Exception('Timeout waiting for file read ' + self._filename)

    async def _run(self):
        pumping = True
        try:
            async with aiofiles.open(self._filename, mode='rb') as file:
                while pumping:
                    chunk = await file.read(self._length)
                    await asyncio.wait_for(self._queue.put(chunk), 60.0)
                    pumping = not io.end_of_stream(chunk)
                    if pumping:
                        self._tracker.processed(chunk)
        except Exception as e:
            logging.error('Error reading ' + self._filename + ': ' + repr(e))
        finally:
            self._tracker.processed(None)
            tasks.task_end(self._task)
            self._task = None
