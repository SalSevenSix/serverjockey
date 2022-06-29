import asyncio
import logging
import typing
from core.util import tasks, util
from core.msg import msgabc, msgext, msgftr
from core.context import contextsvc
from core.system import svrabc


class ServerService(msgabc.AbcSubscriber):
    START = 'ServerService.Start'
    RESTART = 'ServerService.Restart'
    STOP = 'ServerService.Stop'
    DELETE = 'ServerService.Delete'
    DELETE_ME = 'ServerService.DeletedMe'
    SHUTDOWN = 'ServerService.Shutdown'
    SHUTDOWN_RESPONSE = 'ServerService.ShutdownResponse'

    @staticmethod
    def signal_start(mailer: msgabc.Mailer, source: typing.Any):
        mailer.post(source, ServerService.START)

    @staticmethod
    def signal_restart(mailer: msgabc.Mailer, source: typing.Any):
        mailer.post(source, ServerService.RESTART)

    @staticmethod
    def signal_stop(mailer: msgabc.Mailer, source: typing.Any):
        mailer.post(source, ServerService.STOP)

    @staticmethod
    def signal_delete(mailer: msgabc.Mailer, source: typing.Any):
        mailer.post(source, ServerService.DELETE)

    @staticmethod
    async def shutdown(mailer: msgabc.MulticastMailer, source: typing.Any) -> asyncio.Task:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, ServerService.SHUTDOWN)
        return response.data()

    def __init__(self, context: contextsvc.Context, server: svrabc.Server):
        super().__init__(msgftr.NameIn((ServerService.START, ServerService.RESTART, ServerService.STOP,
                                        ServerService.DELETE, ServerService.SHUTDOWN)))
        self._context = context
        self._server = server
        self._queue = asyncio.Queue(maxsize=1)
        self._running = False
        self._task = None
        context.register(ServerStatus(context))
        context.register(self)

    def start(self) -> asyncio.Task:
        self._task = tasks.task_start(self.run(), name=util.obj_to_str(self))
        return self._task

    async def run(self):
        try:
            await self._run()
        finally:
            tasks.task_end(self._task)

    async def _run(self):
        keep_running = True
        while keep_running:
            keep_running = await self._queue.get()   # blocking
            self._running = keep_running
            ServerStatus.notify_running(self._context, self, self._running)
            self._queue.task_done()
            exception = None
            if keep_running:
                try:
                    await self._server.run()
                except Exception as e:
                    exception = e
            self._running = False
            ServerStatus.notify_running(self._context, self, self._running)
            if exception:
                ServerStatus.notify_state(self._context, self, 'EXCEPTION')
                ServerStatus.notify_details(self._context, self, {'exception': repr(exception)})

    async def handle(self, message):
        action = message.name()
        if not self._running and action is ServerService.START:
            self._queue.put_nowait(True)
            await self._queue.join()
            return None
        if self._running and action is ServerService.RESTART:
            self._queue.put_nowait(True)
            await self._server.stop()
            await self._queue.join()
            return None
        if self._running and action is ServerService.STOP:
            await self._server.stop()
            return None
        if action in (ServerService.DELETE, ServerService.SHUTDOWN):
            self._queue.put_nowait(False)
            if self._running:
                await self._server.stop()
            await self._queue.join()
            if self._task:
                await self._task
            if action is ServerService.DELETE:
                self._context.post(self, ServerService.DELETE_ME, self._context)
            if action is ServerService.SHUTDOWN:
                self._context.post(self, ServerService.SHUTDOWN_RESPONSE, self._task, message)
            return True
        return None


class ServerStatus(msgabc.AbcSubscriber):
    UPDATED = 'ServerStatus.Updated'
    UPDATED_FILTER = msgftr.NameIs(UPDATED)
    REQUEST = 'ServerStatus.Request'
    RESPONSE = 'ServerStatus.Response'
    NOTIFY_RUNNING = 'ServerStatus.NotifyRunning'
    NOTIFY_STATE = 'ServerStatus.NotifyState'
    NOTIFY_DETAILS = 'ServerStatus.NotifyDetails'

    @staticmethod
    async def is_running(mailer: msgabc.MulticastMailer, source: typing.Any):
        status = await ServerStatus.get_status(mailer, source)
        return status['running']

    @staticmethod
    async def get_status(mailer: msgabc.MulticastMailer, source: typing.Any):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, ServerStatus.REQUEST)
        return response.data()

    @staticmethod
    def notify_running(mailer: msgabc.Mailer, source: typing.Any, value: bool):
        mailer.post(source, ServerStatus.NOTIFY_RUNNING, value)

    @staticmethod
    def notify_state(mailer: msgabc.Mailer, source: typing.Any, value: str):
        mailer.post(source, ServerStatus.NOTIFY_STATE, value)

    @staticmethod
    def notify_details(mailer: msgabc.Mailer, source: typing.Any, value: typing.Dict[str, typing.Any]):
        mailer.post(source, ServerStatus.NOTIFY_DETAILS, value)

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.NameIn((ServerStatus.REQUEST, ServerStatus.NOTIFY_RUNNING,
                                        ServerStatus.NOTIFY_STATE, ServerStatus.NOTIFY_DETAILS)))
        self._context = context
        self._status: typing.Dict[str, typing.Any] = {'running': False, 'state': 'INIT', 'details': {}}

    async def handle(self, message):
        action = message.name()
        updated = False
        if action is ServerStatus.REQUEST:
            self._context.post(self, ServerStatus.RESPONSE, self._status_copy(), message)
        elif action is ServerStatus.NOTIFY_RUNNING:
            running = message.data()
            if self._status['running'] != running:
                self._status['running'] = running
                if not running:
                    self._status.update({'state': None, 'details': {}})
                updated = True
        elif action is ServerStatus.NOTIFY_STATE:
            self._status['state'] = message.data()
            updated = True
        elif action is ServerStatus.NOTIFY_DETAILS:
            if isinstance(message.data(), dict):
                self._status['details'].update(message.data())
                updated = True
        if updated:
            self._context.post(self, ServerStatus.UPDATED, self._status_copy())
        return None

    def _status_copy(self) -> typing.Dict[str, typing.Any]:
        status = self._status.copy()
        status['details'] = self._status['details'].copy()
        return status
