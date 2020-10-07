from __future__ import annotations
import logging
import typing
import re
from core.util import util
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
        if handler:
            logging.debug(resource.path() + ' => ' + util.obj_to_str(handler))
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
        if handler:
            logging.debug(resource.path() + ' => ' + util.obj_to_str(handler))
        return self

    @staticmethod
    def _unpack(signature: str) -> typing.Tuple[str, httpabc.ResourceKind]:
        if signature.endswith('}'):
            if signature.startswith('{'):
                return signature[1:-1], httpabc.ResourceKind.ARG
            if signature.startswith('x{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_ENCODED
        return signature, httpabc.ResourceKind.PATH


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
        return await util.directory_list_dict(self._path)


class FileHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

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
        result = await msgext.ReadWriteFileSubscriber.write(self._mailer, self._filename, data, self._text)
        if isinstance(result, Exception):
            return {'error': str(result)}
        return httpabc.ResponseBody.NO_CONTENT


class ConfigHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

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
        result = await msgext.ReadWriteFileSubscriber.write(self._mailer, self._filename, data)
        if isinstance(result, Exception):
            return {'error': str(result)}
        return httpabc.ResponseBody.NO_CONTENT


'''
class ReadWriteFileHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, protected: bool = False, text: bool = True):
        self._filename = filename
        self._protected = protected
        self._text = text

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        return await util.read_file(self._filename, text=self._text)

    async def handle_post(self, resource, data):
        await util.write_file(self._filename, data, text=self._text)
        return httpabc.ResponseBody.NO_CONTENT


class ProtectedLineConfigHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, excludes: typing.Collection[str]):
        self._filename = filename
        self._patterns = [re.compile(r) for r in excludes]

    async def handle_get(self, resource, data):
        if not await util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        file = await util.read_file(self._filename)
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
        await util.write_file(self._filename, data)
        return httpabc.ResponseBody.NO_CONTENT
'''
