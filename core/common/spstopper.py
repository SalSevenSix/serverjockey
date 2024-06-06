import typing
import asyncio
from asyncio import subprocess
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import signals
from core.msg import msgabc, msgext
from core.msgc import mc
from core.proc import proch
from core.common import rconsvc


class ServerProcessStopper:

    def __init__(self, mailer: msgabc.MulticastMailer, timeout: float,
                 quit_command: typing.Optional[str] = None,
                 use_rcon: bool = False, use_interrupt: bool = False):
        self._mailer, self._timeout = mailer, timeout
        self._quit_command, self._use_rcon, self._use_interrupt = quit_command, use_rcon, use_interrupt
        self._process_subscriber = _ServerProcessSubscriber()
        mailer.register(self._process_subscriber)

    async def stop(self):
        process = self._process_subscriber.get()
        if not process:
            return
        self._mailer.post(self, mc.ServerProcess.STATE_STOPPING, process)
        catcher = msgext.SingleCatcher(mc.ServerProcess.FILTER_STATES_DOWN, self._timeout)
        self._mailer.register(catcher)
        if self._quit_command:
            if self._use_rcon:
                await rconsvc.RconService.request(self._mailer, self, self._quit_command)
            else:
                await proch.PipeInLineService.request(self._mailer, self, self._quit_command)
        elif self._use_interrupt and process.pid:
            signals.interrupt(process.pid)
        else:
            process.terminate()
        try:
            await catcher.get()
        except asyncio.TimeoutError:
            await signals.kill_tree(process.pid)


class _ServerProcessSubscriber(msgabc.AbcSubscriber):

    def __init__(self):
        super().__init__(mc.ServerProcess.FILTER_STATE_ALL)
        self._process = None

    def get(self) -> subprocess.Process:
        return self._process

    def handle(self, message):
        if mc.ServerProcess.FILTER_STATES_UP.accepts(message) and isinstance(message.data(), subprocess.Process):
            self._process = message.data()
            return None
        if mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._process = None
            return None
        return None
