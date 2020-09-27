import asyncio
import logging
from core import msgext, msgftr, util, system, tasks


class ServerService:
    START = 'ServerService.Start'
    RESTART = 'ServerService.Restart'
    STOP = 'ServerService.Stop'
    DELETE = 'ServerService.Delete'
    SHUTDOWN = 'ServerService.Shutdown'
    SHUTDOWN_RESPONSE = 'ServerService.ShutdownResponse'
    FILTER = msgftr.NameIn((START, RESTART, STOP, DELETE, SHUTDOWN))

    @staticmethod
    def signal_start(mailer, source):
        mailer.post(source, ServerService.START)

    @staticmethod
    def signal_restart(mailer, source):
        mailer.post(source, ServerService.RESTART)

    @staticmethod
    def signal_stop(mailer, source):
        mailer.post(source, ServerService.STOP)

    @staticmethod
    def signal_delete(mailer, source):
        mailer.post(source, ServerService.DELETE)

    @staticmethod
    async def shutdown(mailer, source):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, ServerService.SHUTDOWN)
        return response.get_data()

    def __init__(self, context, server):
        self.context = context
        self.server = server
        self.clientfile = ClientFile(context)
        self.queue = asyncio.Queue(maxsize=1)
        self.running = False
        self.task = None
        context.register(ServerStatus(context))
        context.register(self)

    def start(self):
        self.task = tasks.task_start(self.run(), name=util.obj_to_str(self))
        return self.task

    async def run(self):
        await self.clientfile.write()
        keep_running = True
        while keep_running:
            keep_running = await self.queue.get()  # blocking
            self.running = keep_running
            ServerStatus.notify_running(self.context, self, self.running)
            self.queue.task_done()
            if keep_running:
                await self.server.run()
            self.running = False
            ServerStatus.notify_running(self.context, self, self.running)
        self.clientfile.delete()
        tasks.task_end(self.task)

    def accepts(self, message):
        return ServerService.FILTER.accepts(message)

    async def handle(self, message):
        action = message.get_name()
        if not self.running and action is ServerService.START:
            self.queue.put_nowait(True)
            await self.queue.join()
            return None
        if self.running and action is ServerService.RESTART:
            self.queue.put_nowait(True)
            await self.server.stop()
            await self.queue.join()
            return None
        if self.running and action is ServerService.STOP:
            await self.server.stop()
            return None
        if action in (ServerService.DELETE, ServerService.SHUTDOWN):
            self.queue.put_nowait(False)
            if self.running:
                await self.server.stop()
            await self.queue.join()
            if self.task:
                await self.task
            if action is ServerService.DELETE:
                self.context.post(self, system.SystemService.SERVER_DELETE, self.context)
            if action is ServerService.SHUTDOWN:
                self.context.post(self, ServerService.SHUTDOWN_RESPONSE, self.task, message)
            return True
        return None


class ServerStatus:
    UPDATED = 'ServerStatus.Updated'
    UPDATED_FILTER = msgftr.NameIs(UPDATED)
    REQUEST = 'ServerStatus.Request'
    RESPONSE = 'ServerStatus.Response'
    NOTIFY_RUNNING = 'ServerStatus.NotifyRunning'
    NOTIFY_STATE = 'ServerStatus.NotifyState'
    NOTIFY_DETAILS = 'ServerStatus.NotifyDetails'
    FILTER = msgftr.NameIn((REQUEST, NOTIFY_RUNNING, NOTIFY_STATE, NOTIFY_DETAILS))

    @staticmethod
    async def get_status(mailer, source):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, ServerStatus.REQUEST)
        return response.get_data()

    @staticmethod
    def notify_running(mailer, source, value):
        mailer.post(source, ServerStatus.NOTIFY_RUNNING, value)

    @staticmethod
    def notify_state(mailer, source, value):
        mailer.post(source, ServerStatus.NOTIFY_STATE, value)

    @staticmethod
    def notify_details(mailer, source, value):
        mailer.post(source, ServerStatus.NOTIFY_DETAILS, value)

    def __init__(self, context):
        self.context = context
        self.status = {'running': False, 'state': 'INIT', 'details': {}}

    def accepts(self, message):
        return ServerStatus.FILTER.accepts(message)

    async def handle(self, message):
        action = message.get_name()
        updated = False
        if action is ServerStatus.REQUEST:
            self.context.post(self, ServerStatus.RESPONSE, self._status_copy(), message)
        elif action is ServerStatus.NOTIFY_RUNNING:
            running = message.get_data()
            if self.status['running'] != running:
                self.status['running'] = running
                if not running:
                    self.status.update({'state': None, 'details': {}})
                updated = True
        elif action is ServerStatus.NOTIFY_STATE:
            self.status['state'] = message.get_data()
            updated = True
        elif action is ServerStatus.NOTIFY_DETAILS:
            if isinstance(message.get_data(), dict):
                self.status['details'].update(message.get_data())
                updated = True
        if updated:
            self.context.post(self, ServerStatus.UPDATED, self._status_copy())
        return None

    def _status_copy(self):
        status = self.status.copy()
        status['details'] = self.status['details'].copy()
        return status


class ClientFile:
    UPDATED = 'ClientFile.Updated'

    def __init__(self, context):
        self.context = context
        self.clientfile = util.overridable_full_path(context.config('home'), context.config('clientfile'))

    async def write(self):
        data = util.obj_to_json({
            'SERVERJOCKEY_URL': self.context.config('url'),
            'SERVERJOCKEY_TOKEN': self.context.config('secret')
        })
        if self.clientfile:
            await util.write_file(self.clientfile, data)
            self.context.post(self, ClientFile.UPDATED, self.clientfile)
        logging.debug('Client config: ' + data)
        return self

    def delete(self):
        util.delete_file(self.clientfile)
