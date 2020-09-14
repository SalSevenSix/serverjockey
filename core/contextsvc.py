import importlib

from core import msgsvc


class Context:

    def __init__(self, module, home, executable,
                 logfile=None, clientfile=None,
                 debug=False, host=None, port=9000):
        self.module = importlib.import_module('servers.{}.server'.format(module))
        self.home = home
        self.executable = executable
        self.logfile = logfile if logfile else './serverjockey.log'
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
        return self._relative_path(self.executable)

    def get_logfile(self):
        return self._relative_path(self.logfile)

    def get_clientfile(self):
        return self._relative_path(self.clientfile)

    def relative_path(self, subpath):
        subpath = str(subpath)
        path = [self.home]
        if not subpath.startswith('/'):
            path.append('/')
        path.append(subpath)
        return ''.join(path)

    def _relative_path(self, subpath):
        if subpath is None:
            return None
        if subpath[0] in ('/', '.'):
            return subpath
        return self.relative_path(subpath)

    def register(self, subscriber):
        return self.mailer.register(subscriber)

    def post(self, message):
        return self.mailer.post(message)

    async def shutdown(self):
        await self.mailer.stop()
