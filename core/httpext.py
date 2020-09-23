import logging
import re
from core import httpsvc, proch, util, svrsvc, cmdutil


class ResourceBuilder:

    def __init__(self, name='', handler=None):
        self.current = httpsvc.Resource(None, name, handler)

    def push(self, signature, handler=None):
        name, kind = ResourceBuilder.decode(signature)
        resource = httpsvc.Resource(self.current, name, kind, handler)
        if handler:
            logging.info(resource.get_path() + ' => ' + util.obj_to_str(handler))
        self.current.append(resource)
        self.current = resource
        return self

    def pop(self):
        parent = self.current.get_parent_resource()
        if not parent:
            raise Exception('Cannot pop() root')
        self.current = parent
        return self

    def append(self, signature, handler=None):
        name, kind = ResourceBuilder.decode(signature)
        resource = httpsvc.Resource(self.current, name, kind, handler)
        if handler:
            logging.info(resource.get_path() + ' => ' + util.obj_to_str(handler))
        self.current.append(resource)
        return self

    def build(self):
        while True:
            if self.current.get_parent_resource() is None:
                return self.current
            else:
                self.pop()

    @staticmethod
    def decode(signature):
        name = signature
        kind = httpsvc.Resource.PATH
        if signature.startswith('{') and signature.endswith('}'):
            name = signature.replace('{', '').replace('}', '')
            kind = httpsvc.Resource.ARG
        return name, kind


class DictionaryCoder:

    def __init__(self, coders=None, deep=False):
        self.coders = coders if coders else {}
        if deep:
            raise Exception('Unsupported')

    def append(self, key, coder):
        self.coders.update({key: coder})
        return self

    def process(self, dictionary):
        result = {}
        for key, value in iter(dictionary.items()):
            if key in self.coders:
                coder = self.coders[key]
                if callable(coder):
                    result.update({key: coder(value)})
                elif hasattr(coder, 'encode') and callable(coder.encode):
                    result.update({key: coder.encode(value)})
                elif hasattr(coder, 'decode') and callable(coder.decode):
                    result.update({key: coder.decode(value)})
            else:
                result.update({key: value})
        return result


class PipeInLineNoContentPostHandler:

    def __init__(self, mailer, source, commands, decoder=DictionaryCoder()):
        assert isinstance(commands, cmdutil.CommandLines)
        assert isinstance(decoder, DictionaryCoder)
        self.mailer = mailer
        self.source = source
        self.commands = commands
        self.decoder = decoder

    def get_decoder(self):
        return self.decoder

    async def handle_post(self, resource, data):
        cmdline = self.commands.get(data)
        if not cmdline:
            return httpsvc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self.mailer, self.source, cmdline.build())
        return httpsvc.ResponseBody.NO_CONTENT


class ServerStatusHandler:

    def __init__(self, mailer):
        self.mailer = mailer

    async def handle_get(self, resource, data):
        return await svrsvc.ServerStatus.get_status(self.mailer, self)


class ServerCommandHandler:
    COMMANDS = util.attr_dict(svrsvc.ServerService, ('start', 'restart', 'stop', 'shutdown'))

    def __init__(self, mailer):
        self.mailer = mailer

    async def handle_post(self, resource, data):
        command = util.get('command', data)
        if command is None or command not in ServerCommandHandler.COMMANDS:
            return httpsvc.ResponseBody.BAD_REQUEST
        ServerCommandHandler.COMMANDS[command](self.mailer, self)
        return httpsvc.ResponseBody.NO_CONTENT


class ReadWriteFileHandler:

    def __init__(self, filename, protected=False, text=True):
        self.filename = filename
        self.protected = protected
        self.text = text

    async def handle_get(self, resource, data):
        if self.protected and not httpsvc.is_secure(data):
            return httpsvc.ResponseBody.UNAUTHORISED
        if not util.file_exists(self.filename):
            return httpsvc.ResponseBody.NOT_FOUND
        return await util.read_file(self.filename, text=self.text)

    async def handle_post(self, resource, data):
        await util.write_file(self.filename, data, text=self.text)
        return httpsvc.ResponseBody.NO_CONTENT


class ProtectedLineConfigHandler:

    def __init__(self, filename, excludes):
        self.filename = filename
        self.patterns = []
        for regex in iter(excludes):
            self.patterns.append(re.compile(regex))

    async def handle_get(self, resource, data):
        if not util.file_exists(self.filename):
            return httpsvc.ResponseBody.NOT_FOUND
        file = await util.read_file(self.filename)
        if httpsvc.is_secure(data):
            return file
        file = file.split('\n')
        result = []
        for line in iter(file):
            exclude = False
            for pattern in iter(self.patterns):
                if pattern.match(line) is not None:
                    exclude = True
            if not exclude:
                result.append(line)
        return util.to_text(result)

    async def handle_post(self, resource, data):
        await util.write_file(self.filename, data)
        return httpsvc.ResponseBody.NO_CONTENT
