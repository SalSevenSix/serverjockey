import abc
import logging
import asyncio
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import cmdutil, util, tasks
from core.msg import msgabc
from core.msgc import mc
from core.http import httpabc
from core.system import svrsvc
from core.proc import proch


class ServerStateSubscriber(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(mc.ServerProcess.FILTER_STATE_ALL)
        self._mailer = mailer

    def handle(self, message):
        name, data = message.name(), message.data()
        state = util.lchop(name, '.').upper()
        details = dict(error=str(data)) if name is mc.ServerProcess.STATE_EXCEPTION else None
        svrsvc.ServerStatus.notify_status(self._mailer, self, state, details)
        return None


class ConsoleCommandHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, commands: cmdutil.CommandLines):
        self._mailer, self._commands = mailer, commands

    async def handle_post(self, resource, data):
        cmdline = self._commands.get(data)
        if not cmdline:
            return httpabc.ResponseBody.BAD_REQUEST
        await proch.PipeInLineService.request(self._mailer, self, cmdline.build())
        return httpabc.ResponseBody.NO_CONTENT


class SayFormatter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def cmdline(self, player: str, line: str) -> str:
        pass


class TemplateSayFormatter(SayFormatter):

    def __init__(self, template: str):
        self._template = template

    def cmdline(self, player: str, line: str) -> str:
        return self._template.format(player=player, line=line)


class SayHandler(httpabc.PostHandler):

    def __init__(self, mailer: msgabc.MulticastMailer, formatter: SayFormatter | str):
        self._mailer = mailer
        self._formatter = TemplateSayFormatter(formatter) if isinstance(formatter, str) else formatter

    async def handle_post(self, resource, data):
        player, text = util.get('player', data), util.get('text', data)
        player, text = player.strip() if player else player, text.strip() if text else text
        if not text:
            return httpabc.ResponseBody.NO_CONTENT
        if not player:
            return httpabc.ResponseBody.BAD_REQUEST
        if player == '@':  # This is the Chatbot
            lines = text.split('\n')
        else:
            lines = util.split_lines(text, lines_limit=5, total_char_limit=280)
        if not lines:
            return httpabc.ResponseBody.BAD_REQUEST
        for line in [o.strip() for o in lines if o]:
            await proch.PipeInLineService.request(self._mailer, self, self._formatter.cmdline(player, line))
        return httpabc.ResponseBody.NO_CONTENT


class TimedConsoleCommand:

    def __init__(self, mailer: msgabc.MulticastMailer, cmdline: str, seconds: float):
        self._mailer, self._cmdline, self._seconds = mailer, cmdline, seconds
        self._queue = asyncio.Queue(maxsize=1)
        self._running, self._task = False, None

    def start(self):
        if self._running or self._seconds == 0.0:
            return
        self._running = True
        self._task = tasks.task_start(self._run(), self)

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._queue.put_nowait(None)

    async def _run(self):
        try:
            running = True
            while running and self._running:
                running = await self._next()
                if running and self._running:
                    await proch.PipeInLineService.request(self._mailer, self, self._cmdline)
        except Exception as e:
            logging.debug('TimedConsoleCommand(%s) %s', self._cmdline, repr(e))
        finally:
            self._running = False
            util.clear_queue(self._queue)
            tasks.task_end(self._task)

    async def _next(self) -> bool:
        try:
            await asyncio.wait_for(self._queue.get(), self._seconds)
            self._queue.task_done()
            return False
        except asyncio.TimeoutError:
            return True
