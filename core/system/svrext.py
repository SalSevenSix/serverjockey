from core.util import util
from core.context import contextsvc
from core.msg import msgabc
from core.http import httpabc
from core.system import svrsvc


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


class ServerRunningLock(msgabc.AbcSubscriber):
    BLOCK = 'ServerRunningLock.Block'

    def __init__(self, mailer: msgabc.MulticastMailer, delegate: msgabc.Subscriber):
        super().__init__(delegate)
        self._mailer = mailer
        self._delegate = delegate

    async def handle(self, message):
        source = message.source()
        if await svrsvc.ServerStatus.is_running(self._mailer, source):
            self._mailer.post(source, ServerRunningLock.BLOCK, Exception('Server is running'), message)
            return None
        return await msgabc.try_handle('MonitorSubscriber', self._delegate, message)


class ClientFile:
    WRITTEN = 'ClientFile.Written'

    def __init__(self, context: contextsvc.Context, clientfile: str):
        self._context = context
        self._clientfile = clientfile

    def path(self):
        return self._clientfile

    async def write(self):
        data = util.obj_to_json({
            'SERVER_URL': self._context.config('baseurl'),
            'SERVER_TOKEN': self._context.config('secret')
        })
        await util.write_file(self._clientfile, data)
        self._context.post(self, ClientFile.WRITTEN, self._clientfile)

    async def delete(self):
        # TODO silently delete?
        await util.delete_file(self._clientfile)
