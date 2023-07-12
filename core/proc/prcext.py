import typing
import asyncio
from asyncio import subprocess
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import cmdutil, util, signals
from core.msg import msgabc, msgext
from core.http import httpabc
from core.system import svrsvc
from core.proc import proch


class ServerStateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(proch.ServerProcess.FILTER_STATE_ALL)
        self._mailer = mailer

    def handle(self, message):
        name = message.name()
        state = util.left_chop_and_strip(name, '.').upper()
        svrsvc.ServerStatus.notify_state(self._mailer, self, state)
        if name is proch.ServerProcess.STATE_EXCEPTION:
            svrsvc.ServerStatus.notify_details(self._mailer, self, {'error': str(message.data())})
        return None


class ConsoleCommandHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, commands: cmdutil.CommandLines):
        self._mailer = mailer
        self._commands = commands

    async def handle_post(self, resource, data):
        cmdline = self._commands.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class ServerProcessStopper:

    def __init__(self,
                 mailer: msgabc.MulticastMailer,
                 timeout: float,
                 quit_command: typing.Optional[str] = None,
                 use_interrupt: bool = False):
        self._mailer = mailer
        self._timeout = timeout
        self._quit_command = quit_command
        self._use_interrupt = use_interrupt
        self._process_subscriber = _ServerProcessSubscriber()
        mailer.register(self._process_subscriber)

    async def stop(self):
        process = self._process_subscriber.get()
        if not process:
            return
        self._mailer.post(self, proch.ServerProcess.STATE_STOPPING, process)
        catcher = msgext.SingleCatcher(proch.ServerProcess.FILTER_STATES_DOWN, self._timeout)
        self._mailer.register(catcher)
        if self._quit_command:
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
        super().__init__(proch.ServerProcess.FILTER_STATE_ALL)
        self._process = None

    def get(self) -> subprocess.Process:
        return self._process

    def handle(self, message):
        if proch.ServerProcess.FILTER_STATES_UP.accepts(message) and isinstance(message.data(), subprocess.Process):
            self._process = message.data()
            return None
        if proch.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._process = None
            return None
        return None
