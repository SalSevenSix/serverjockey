import importlib

from core import msgsvc


class Context:

    def __init__(self, module, home, executable, clientfile=None, debug=False, host=None, port=9000):
        self.module = importlib.import_module('servers.{}.server'.format(module))
        self.home = home
        self.executable = executable
        self.clientfile = clientfile
        self.debug = debug
        self.host = host
        self.port = port
        self.mailer = msgsvc.MulticastMailer()
        self.mailer.start()

    def create_server(self):
        return self.module.Server(self)

    def is_debug(self):
        return self.debug

    def get_home(self):
        return self.home

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_executable(self):
        if self.executable[:1] in ('/', '.'):
            return self.executable
        return self.relative_path(self.executable)

    def get_clientfile(self):
        if self.clientfile is None:
            return None
        if self.clientfile[:1] in ('/', '.'):
            return self.clientfile
        return self.relative_path(self.clientfile)

    def relative_path(self, subpath):
        path = [self.home]
        subpath = str(subpath)
        if not subpath.startswith('/'):
            path.append('/')
        path.append(subpath)
        return ''.join(path)

    def register(self, subscriber):
        return self.mailer.register(subscriber)

    def post(self, message):
        return self.mailer.post(message)

    async def shutdown(self):
        await self.mailer.stop()
