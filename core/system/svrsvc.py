from __future__ import annotations
import logging
import asyncio
import typing
# ALLOW const.* util.* msg*.* context.* http.* system.svrabc
from core.util import tasks, util, dtutil
from core.msg import msgabc, msgext, msgftr
from core.msgc import mc
from core.context import contextsvc
from core.system import svrabc


class ServerService(msgabc.AbcSubscriber):
    START, RESTART, STOP = 'ServerService.Start', 'ServerService.Restart', 'ServerService.Stop'
    DELETE, DELETE_ME = 'ServerService.Delete', 'ServerService.DeletedMe'
    SHUTDOWN, SHUTDOWN_RESPONSE = 'ServerService.Shutdown', 'ServerService.ShutdownResponse'
    CLEANUP_FILTER = msgftr.NameIn((DELETE, SHUTDOWN))

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
        response = await msgext.SynchronousMessenger(mailer).request(source, ServerService.SHUTDOWN)
        return response.data()

    def __init__(self, context: contextsvc.Context, server: svrabc.Server):
        super().__init__(msgftr.NameIn((
            ServerService.START, ServerService.RESTART, ServerService.STOP,
            ServerService.DELETE, ServerService.SHUTDOWN)))
        self._context, self._server = context, server
        self._queue = asyncio.Queue(maxsize=1)
        self._running, self._task = False, None
        context.register(ServerStatus(context))
        context.register(self)

    def start(self) -> asyncio.Task:
        self._task = tasks.task_start(self.run(), self)
        return self._task

    async def run(self):
        try:
            await self._run()
        finally:
            tasks.task_end(self._task)

    async def _run(self):
        identity = self._context.config('identity')
        controller = _RunController(True, False, False)
        while controller.looping():
            if controller.daemon() and self._queue.empty():
                self._running = controller.call_run()
            else:
                controller = await self._queue.get()
                self._running = controller.call_run()
                self._queue.task_done()
            if self._running:
                logging.debug('STARTING instance ' + identity)
                ServerStatus.notify_running(self._context, self, self._running)
                start = dtutil.now_millis()
                try:
                    await self._server.run()
                except Exception as e:
                    ServerStatus.notify_status(self._context, self, 'EXCEPTION', {'error': str(e)})
                    logging.warning('EXCEPTION instance ' + identity + ' [' + repr(e) + ']')
                finally:
                    self._running = False
                    controller.check_uptime(dtutil.now_millis() - start)
                    ServerStatus.notify_running(self._context, self, self._running)
                    logging.debug('STOPPED instance ' + identity)

    async def handle(self, message):
        action = message.name()
        if not self._running and action is ServerService.START:
            self._queue.put_nowait(_RunController(True, True, self._is_daemon()))
            await self._queue_join()
            return None
        if self._running and action is ServerService.RESTART:
            self._queue.put_nowait(_RunController(True, True, self._is_daemon()))
            await self._server_stop()
            await self._queue_join()
            return None
        if self._running and action is ServerService.STOP:
            self._queue.put_nowait(_RunController(True, False, False))
            await self._server_stop()
            await self._queue_join()
            return None
        if action in (ServerService.DELETE, ServerService.SHUTDOWN):
            self._queue.put_nowait(_RunController(False, False, False))
            await self._server_stop()
            await self._queue_join()
            await tasks.wait_for(self._task, 10.0)
            if action is ServerService.DELETE:
                self._context.root().post(self, ServerService.DELETE_ME, self._context)
            if action is ServerService.SHUTDOWN:
                self._context.post(self, ServerService.SHUTDOWN_RESPONSE, self._task, message)
            return True
        return None

    def _is_daemon(self):
        auto = self._context.config('auto')
        return auto and auto > 1

    async def _server_stop(self):
        if not self._running:
            return
        try:
            await asyncio.wait_for(self._server.stop(), 30.0)
        except asyncio.TimeoutError:
            pass

    async def _queue_join(self):
        try:
            await asyncio.wait_for(self._queue.join(), 10.0)
        except asyncio.TimeoutError:
            util.clear_queue(self._queue)


class _RunController:

    def __init__(self, looping: bool, call_run: bool, daemon: bool):
        self._looping = looping
        self._call_run = looping and call_run
        self._daemon, self._daemon_attempts = daemon, 3

    def check_uptime(self, uptime: int):
        if not self._daemon:
            return
        if uptime < 10000:
            self._daemon_attempts -= 1
            if self._daemon_attempts <= 0:
                self._daemon = False
        else:
            self._daemon_attempts = 3

    def looping(self) -> bool:
        return self._looping

    def call_run(self) -> bool:
        return self._call_run

    def daemon(self) -> bool:
        return self._daemon


class ServerStatus(msgabc.AbcSubscriber):
    REQUEST, RESPONSE = 'ServerStatus.Request', 'ServerStatus.Response'
    NOTIFY_RUNNING = 'ServerStatus.NotifyRunning'
    NOTIFY_STATUS = 'ServerStatus.NotifyStatus'
    RUNNING_FALSE_FILTER = msgftr.And(msgftr.NameIs(NOTIFY_RUNNING), msgftr.DataEquals(False))

    @staticmethod
    async def get_status(mailer: msgabc.MulticastMailer, source: typing.Any):
        response = await msgext.SynchronousMessenger(mailer).request(source, ServerStatus.REQUEST)
        return response.data()

    @staticmethod
    def notify_running(mailer: msgabc.Mailer, source: typing.Any, running: bool):
        mailer.post(source, ServerStatus.NOTIFY_RUNNING, running)

    @staticmethod
    def notify_status(
            mailer: msgabc.Mailer, source: typing.Any,
            state: str | None, details: typing.Optional[typing.Dict[str, typing.Any]]):
        status = {}
        if state:
            status['state'] = state
        if details:
            status['details'] = details
        mailer.post(source, ServerStatus.NOTIFY_STATUS, status)

    @staticmethod
    def notify_state(mailer: msgabc.Mailer, source: typing.Any, state: str):
        ServerStatus.notify_status(mailer, source, state, None)

    @staticmethod
    def notify_details(mailer: msgabc.Mailer, source: typing.Any, details: typing.Dict[str, typing.Any]):
        ServerStatus.notify_status(mailer, source, None, details)

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.NameIn((
            ServerStatus.REQUEST, ServerStatus.NOTIFY_RUNNING, ServerStatus.NOTIFY_STATUS)))
        self._context = context
        self._status = _Status(context)

    def handle(self, message):
        action = message.name()
        if action is ServerStatus.REQUEST:
            self._context.post(self, ServerStatus.RESPONSE, self._status.asdict(), message)
            return None
        data, updated = message.data(), False
        if action is ServerStatus.NOTIFY_RUNNING:
            updated = self._status.notify_running(data)
        elif action is ServerStatus.NOTIFY_STATUS:
            updated = self._status.notify_status(data)
        if updated:
            self._context.post(self, mc.ServerStatus.UPDATED, self._status.asdict())
        return None


class _Status:
    READY = 'READY'

    def __init__(self, context: contextsvc.Context):
        self._context = context
        self._running, self._state = False, _Status.READY
        self._details, self._startmillis = {}, 0

    def notify_running(self, running) -> bool:
        if self._running == running:
            return False
        self._running = running
        if running:
            self._details = {}
            self._startmillis = dtutil.now_millis()
        else:
            self._startmillis = 0
        return True

    def notify_status(self, status) -> bool:
        if not isinstance(status, dict):
            return False
        state, details = util.get('state', status), util.get('details', status)
        state_updated = self._notify_state(state)
        details_updated = self._notify_details(details)
        return state_updated or details_updated

    def _notify_state(self, state) -> bool:
        if state is None or state == self._state:
            return False
        self._state = state
        if state == _Status.READY:
            self._details = {}
        return True

    def _notify_details(self, details) -> bool:
        if details is None or not isinstance(details, dict):
            return False
        self._details.update(details)
        return True

    def asdict(self) -> typing.Dict[str, typing.Any]:
        status = {'instance': self._context.config('identity'), 'running': self._running,
                  'state': self._state, 'details': self._details.copy()}
        auto = self._context.config('auto')
        status['auto'] = auto if auto else 0
        if self._startmillis > 0:
            status['startmillis'] = self._startmillis
            status['uptime'] = dtutil.now_millis() - self._startmillis
        return status
