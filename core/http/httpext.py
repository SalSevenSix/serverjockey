import asyncio
import typing
import re
import aiofiles
from core.util import util, tasks
from core.msg import msgabc, msgext, msgftr
from core.http import httpabc, httpcnt, httpsubs


class LoginHandler(httpabc.PostHandler):

    def __init__(self, secret: str):
        self._secret = secret

    def handle_post(self, resource, data):
        return self._secret


class MessengerHandler(httpabc.AsyncPostHandler):

    def __init__(self,
                 mailer: msgabc.MulticastMailer,
                 name: str,
                 data: typing.Optional[httpabc.ABC_DATA_GET] = None,
                 selector: typing.Optional[httpsubs.Selector] = None):
        self._mailer = mailer
        self._name = name
        self._data = data
        self._selector = selector

    async def handle_post(self, resource, data):
        messenger = msgext.SynchronousMessenger(self._mailer)
        subscription_path, source = None, util.obj_to_str(messenger)
        data['resource'] = resource.name()
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
            return {'error': str(result)}
        if subscription_path:
            return {'url': util.get('baseurl', data, '') + subscription_path}
        if result is False:
            return httpabc.ResponseBody.BAD_REQUEST
        if result is None:
            return httpabc.ResponseBody.NOT_FOUND
        if result is True:
            return httpabc.ResponseBody.NO_CONTENT
        return result


class MessengerConfigHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, filename: str,
                 protection: typing.Union[bool, typing.Collection[str]] = False):
        self._mailer = mailer
        self._filename = filename
        self._protected = protection if isinstance(protection, bool) else False
        self._patterns = [] if isinstance(protection, bool) else [re.compile(r) for r in protection]

    async def handle_get(self, resource, data):
        if self._protected and not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        content = await msgext.ReadWriteFileSubscriber.read(self._mailer, self._filename)
        if isinstance(content, Exception):
            return {'error': str(content)}
        if len(self._patterns) == 0 or httpcnt.is_secure(data):
            return content
        result = []
        for line in iter(content.split('\n')):
            exclude = False
            for pattern in iter(self._patterns):
                if pattern.match(line) is not None:
                    exclude = True
            if not exclude:
                result.append(line)
        return '\n'.join(result)

    async def handle_post(self, resource, data):
        body = util.get('body', data)
        if not isinstance(body, str):
            return httpabc.ResponseBody.BAD_REQUEST
        result = await msgext.ReadWriteFileSubscriber.write(self._mailer, self._filename, body)
        if isinstance(result, Exception):
            return {'error': str(result)}
        return httpabc.ResponseBody.NO_CONTENT


class FileSystemHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, path: str, tail: typing.Optional[str] = None, protected: bool = True):
        self._path = path
        self._tail = tail
        self._protected = protected

    async def handle_get(self, resource, data):
        if self._protected and not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        path = self._path + '/' + data[self._tail] if self._tail else self._path
        if await util.file_exists(path):
            content_type = httpcnt.ContentTypeImpl.lookup(path)
            size = await util.file_size(path)
            if content_type.is_text_type() and size < 1048576:
                return await util.read_file(path)
            return _FileByteStream(path)
        if await util.directory_exists(path):
            return await util.directory_list_dict(path, data['baseurl'] + resource.path(data))
        return httpabc.ResponseBody.NOT_FOUND

    async def handle_post(self, resource, data):
        path = self._path + '/' + data[self._tail] if self._tail else self._path
        body = util.get('body', data)
        if not body:
            if await util.file_exists(path):
                await util.delete_file(path)
                return httpabc.ResponseBody.NO_CONTENT
            return httpabc.ResponseBody.BAD_REQUEST
        if await util.directory_exists(path):
            return httpabc.ResponseBody.BAD_REQUEST
        if not await util.directory_exists('/'.join(path.split('/')[0:-1])):
            return httpabc.ResponseBody.BAD_REQUEST
        if isinstance(body, str):
            await util.write_file(path, body)
            return httpabc.ResponseBody.NO_CONTENT
        if isinstance(body, httpabc.ByteStream):
            await util.stream_write_file(path, body)
            return httpabc.ResponseBody.NO_CONTENT
        return httpabc.ResponseBody.BAD_REQUEST


class _FileByteStream(httpabc.ByteStream):

    def __init__(self, filename: str):
        self._name = filename.split('/')[-1]
        self._filename = filename
        self._content_type = httpcnt.ContentTypeImpl.lookup(filename)
        self._queue = asyncio.Queue(maxsize=1)
        self._task = None
        self._length = -1

    def name(self) -> str:
        return self._name

    def content_type(self) -> httpabc.ContentType:
        return self._content_type

    async def content_length(self) -> int:
        return await util.file_size(self._filename)

    async def read(self, length: int = -1) -> bytes:
        if self._task is None:
            self._length = length
            self._task = tasks.task_start(self._run(), name=self._filename)
        return await self._queue.get()

    async def _run(self):
        async with aiofiles.open(self._filename, mode='rb') as file:
            pumping = True
            while pumping:
                chunk = await file.read(self._length)
                await self._queue.put(chunk)
                pumping = chunk is not None and chunk != b''
        tasks.task_end(self._task)
        self._task = None
