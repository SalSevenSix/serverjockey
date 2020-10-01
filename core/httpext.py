from __future__ import annotations
import logging
import re
import typing
from core import httpabc, httpsvc, proch, util, svrsvc, msgabc, cmdutil


class ResourceBuilder:

    def __init__(self, name: str = ''):
        self._current = httpsvc.WebResource(name)

    def push(self, signature: str, handler: typing.Optional[httpabc.ABC_HANDLER] = None) -> ResourceBuilder:
        name, kind = ResourceBuilder._unpack(signature)
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

    def build(self) -> httpabc.Resource:
        while True:
            if self._current.parent() is None:
                return self._current
            else:
                self.pop()

    @staticmethod
    def _unpack(signature: str) -> typing.Tuple[str, httpabc.ResourceKind]:
        if signature.endswith('}'):
            if signature.startswith('{'):
                return signature[1:-1], httpabc.ResourceKind.ARG
            if signature.startswith('x{'):
                return signature[2:-1], httpabc.ResourceKind.ARG_ENCODED
        return signature, httpabc.ResourceKind.PATH


class PipeInLineNoContentPostHandler(httpabc.AsyncPostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any, commands: cmdutil.CommandLines):
        self._mailer = mailer
        self._source = source
        self._commands = commands

    async def handle_post(self, resource, data):
        cmdline = self._commands.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self._source, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class ServerStatusHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await svrsvc.ServerStatus.get_status(self._mailer, self)


class ServerCommandHandler(httpabc.PostHandler):
    COMMANDS = util.callable_dict(
        svrsvc.ServerService,
        ('signal_start', 'signal_restart', 'signal_stop', 'signal_delete'))

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def handle_post(self, resource, data):
        command = 'signal_' + str(util.get('command', data))
        if command not in ServerCommandHandler.COMMANDS:
            return httpabc.ResponseBody.BAD_REQUEST
        ServerCommandHandler.COMMANDS[command](self._mailer, self)
        return httpabc.ResponseBody.NO_CONTENT


class ReadWriteFileHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, protected: bool = False, text: bool = True):
        self._filename = filename
        self._protected = protected
        self._text = text

    async def handle_get(self, resource, data):
        if self._protected and not httpabc.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if not util.file_exists(self._filename):
            return httpabc.ResponseBody.NOT_FOUND
        return await util.read_file(self._filename, text=self._text)

    async def handle_post(self, resource, data):
        await util.write_file(self._filename, data, text=self._text)
        return httpabc.ResponseBody.NO_CONTENT


class ProtectedLineConfigHandler(httpabc.AsyncGetHandler, httpabc.AsyncPostHandler):

    def __init__(self, filename: str, excludes: typing.Collection[str]):
        self._filename = filename
        self._patterns: typing.List[re.Pattern] = []
        for regex in iter(excludes):
            self._patterns.append(re.compile(regex))

    async def handle_get(self, resource, data):
        if not util.file_exists(self._filename):
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
