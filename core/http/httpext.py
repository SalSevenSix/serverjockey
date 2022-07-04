from __future__ import annotations
import asyncio
import logging
import typing
import re
import aiofiles
from core.util import util, tasks
from core.msg import msgabc, msgext, msgftr
from core.http import httpabc, httpsvc, httpsubs


class ResourceBuilder:

    def __init__(self, resource: httpabc.Resource):
        self._current = resource

    def push(self, signature: str, handler: typing.Optional[httpabc.ABC_HANDLER] = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = self._current.child(name)
        if resource is None:
            resource = httpsvc.WebResource(name, kind, handler)
        self._current.append(resource)
        self._current = resource
        ResourceBuilder._log_binding(resource, handler)
        return self

    def pop(self) -> ResourceBuilder:
        parent = self._current.parent()
        if not parent:
            raise Exception('Cannot pop() root')
        self._current = parent
        return self

    def append(self, signature: str, handler: typing.Optional[httpabc.ABC_HANDLER] = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
        resource = httpsvc.WebResource(name, kind, handler)
        self._current.append(resource)
        ResourceBuilder._log_binding(resource, handler)
        return self

    @staticmethod
    def _unpack(signature: str) -> typing.Tuple[str, httpabc.ResourceKind]:
        if signature.endswith('}'):
            if signature.startswith('{'):
                return signature[1:-1], httpabc.ResourceKind.ARG
            if signature.startswith('x{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_ENCODED
        return signature, httpabc.ResourceKind.PATH

    @staticmethod
    def _log_binding(resource: httpabc.Resource, handler: typing.Optional[httpabc.ABC_HANDLER]):
        if handler is None:
            return
        allows = ''
        if resource.allows(httpabc.Method.GET):
            allows += httpabc.Method.GET.value
        if resource.allows(httpabc.Method.POST):
            allows += '|' if allows else ''
            allows += httpabc.Method.POST.value
        logging.debug('trs> BIND {} {} => {}'.format(resource.path(), allows, util.obj_to_str(handler)))


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
        url, source = None, util.obj_to_str(messenger)
        if isinstance(data, dict):
            data['resource'] = resource.name()
            if self._data:
                data = {**self._data, **data}
        if self._selector:
            url = await httpsubs.HttpSubscriptionService.subscribe(self._mailer, source, httpsubs.Selector(
                msg_filter=msgftr.And(msgftr.SourceIs(source), self._selector.msg_filter),
                completed_filter=msgftr.And(msgftr.SourceIs(source), self._selector.completed_filter),
                transformer=self._selector.transformer, aggregator=self._selector.aggregator))
        response = await messenger.request(source, self._name, data)
        result = response.data()
        if isinstance(result, Exception):
            httpsubs.HttpSubscriptionService.unsubscribe(self._mailer, source, url)
            return {'error': str(result)}
        if url:
            return {'url': url}
        if result is False:
            return httpabc.ResponseBody.BAD_REQUEST
        if result is None:
            return httpabc.ResponseBody.NOT_FOUND
        if result is True:
            return httpabc.ResponseBody.NO_CONTENT
        return result


class DirectoryListHandler(httpabc.AsyncGetHandler):

    def __init__(self, path: str):
        self._path = path

    async def handle_get(self, resource, data):
        return await util.directory_list_dict(self._path, resource.path())


class MessengerFileHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, filename: str, protected: bool = False, text: bool = True):
        self._mailer = mailer
        self._filename = filename
        self._protected = protected
        self._text = text

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        result = await msgext.ReadWriteFileSubscriber.read(self._mailer, self._filename, self._text)
        if isinstance(result, Exception):
            return {'error': str(result)}
        return result

    async def handle_post(self, resource, data):
        result = await msgext.ReadWriteFileSubscriber.write(self._mailer, self._filename, data['body'], self._text)
        if isinstance(result, Exception):
            return {'error': str(result)}
        return httpabc.ResponseBody.NO_CONTENT


class MessengerConfigHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, filename: str, excludes: typing.Collection[str]):
        self._mailer = mailer
        self._filename = filename
        self._patterns = [re.compile(r) for r in excludes]

    async def handle_get(self, resource, data):
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        file = await msgext.ReadWriteFileSubscriber.read(self._mailer, self._filename)
        if isinstance(file, Exception):
            return {'error': str(file)}
        if httpabc.is_secure(data):
            return file
        file = file.split('\n')
        result = []
        for line in iter(file):
            exclude = False
            for pattern in iter(self._patterns):
                if pattern.match(line) is not None:
                    exclude = True
            if not exclude:
                result.append(line)
        return '\n'.join(result)

    async def handle_post(self, resource, data):
        result = await msgext.ReadWriteFileSubscriber.write(self._mailer, self._filename, data['body'])
        if isinstance(result, Exception):
            return {'error': str(result)}
        return httpabc.ResponseBody.NO_CONTENT


class FileHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, protected: bool = False, text: bool = True):
        self._filename = filename
        self._protected = protected
        self._text = text

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        return await util.read_file(self._filename, self._text)

    async def handle_post(self, resource, data):
        await util.write_file(self._filename, data['body'], self._text)
        return httpabc.ResponseBody.NO_CONTENT


class FileStreamHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, protected: bool = False):
        self._name = filename.split('/')[-1]
        self._filename = filename
        self._protected = protected

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        return _FileByteStream(self._name, self._filename)

    async def handle_post(self, resource, data):
        await util.stream_write_file(data['body'], self._filename)
        return httpabc.ResponseBody.NO_CONTENT


class DirectoryStreamHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, directory: str, protected: bool = False):
        self._directory = directory
        self._protected = protected

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        filename = util.get('filename', data)
        if filename is None:
            return httpabc.ResponseBody.BAD_REQUEST
        path = self._directory + '/' + filename
        if not await util.file_exists(path):
            return httpabc.ResponseBody.NOT_FOUND
        return _FileByteStream(filename, path)

    async def handle_post(self, resource, data):
        filename, body = util.get('filename', data), util.get('body', data)
        if filename is None:
            return httpabc.ResponseBody.BAD_REQUEST
        if body and not isinstance(body, httpabc.ByteStream):
            return httpabc.ResponseBody.BAD_REQUEST
        path = self._directory + '/' + filename
        if body is None:
            await util.delete_file(path)
            return httpabc.ResponseBody.NO_CONTENT
        await util.stream_write_file(body, path)
        return httpabc.ResponseBody.NO_CONTENT


class _FileByteStream(httpabc.ByteStream):

    def __init__(self, name: str, filename: str):
        self._name = name
        self._filename = filename
        self._queue = asyncio.Queue(maxsize=1)
        self._task = None
        self._length = -1

    def name(self) -> str:
        return self._name

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
