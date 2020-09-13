import asyncio

from core import msgext, msgftr, msgsvc


class ServerService:
    START = 'ServerService.Start'
    RESTART = 'ServerService.Restart'
    STOP = 'ServerService.Stop'
    SHUTDOWN = 'ServerService.Shutdown'
    FILTER = msgftr.NameIn((START, RESTART, STOP, SHUTDOWN))

    @staticmethod
    def start(mailer, source):
        mailer.post((source, ServerService.START))

    @staticmethod
    def restart(mailer, source):
        mailer.post((source, ServerService.RESTART))

    @staticmethod
    def stop(mailer, source):
        mailer.post((source, ServerService.STOP))

    @staticmethod
    def shutdown(mailer, source):
        mailer.post((source, ServerService.SHUTDOWN))

    def __init__(self, context, server):
        self.context = context
        self.server = server
        self.queue = asyncio.Queue(maxsize=1)
        self.running = False
        context.register(ServerStatus(context))
        context.register(self)

    async def run(self):
        rc = 0
        keep_running = True
        while keep_running:
            keep_running = await self.queue.get()   # blocking
            self.running = keep_running
            ServerStatus.notify_running(self.context, self, self.running)
            self.queue.task_done()
            if keep_running:
                rc = await self.server.run()
            self.running = False
            ServerStatus.notify_running(self.context, self, self.running)
        return rc

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
        if action is ServerService.SHUTDOWN:
            self.queue.put_nowait(False)
            if self.running:
                await self.server.stop()
            await self.queue.join()
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
    async def request(mailer, source):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, ServerStatus.REQUEST))
        return response.get_data()

    @staticmethod
    def notify_running(mailer, source, value):
        mailer.post((source, ServerStatus.NOTIFY_RUNNING, value))

    @staticmethod
    def notify_state(mailer, source, value):
        mailer.post((source, ServerStatus.NOTIFY_STATE, value))

    @staticmethod
    def notify_details(mailer, source, value):
        mailer.post((source, ServerStatus.NOTIFY_DETAILS, value))

    def __init__(self, context):
        self.context = context
        self.status = {'running': False, 'state': 'INIT', 'details': {}}

    def accepts(self, message):
        return ServerStatus.FILTER.accepts(message)

    async def handle(self, message):
        action = message.get_name()
        updated = False
        if action is ServerStatus.REQUEST:
            self.context.post((self, ServerStatus.RESPONSE, self._status_copy(), message))
        elif action is ServerStatus.NOTIFY_RUNNING:
            running = message.get_data()
            self.status['running'] = running
            if not running:
                self.status['details'] = {}
            updated = True
        elif action is ServerStatus.NOTIFY_STATE:
            self.status['state'] = message.get_data()
            updated = True
        elif action is ServerStatus.NOTIFY_DETAILS:
            if isinstance(message.get_data(), dict):
                self.status['details'].update(message.get_data())
                updated = True
        if updated:
            self.context.post((self, ServerStatus.UPDATED, self._status_copy()))
        return None

    def _status_copy(self):
        status = self.status.copy()
        status['details'] = self.status['details'].copy()
        return status
