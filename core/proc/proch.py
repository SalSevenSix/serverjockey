from __future__ import annotations
import logging
import typing
import asyncio
from asyncio import streams
# ALLOW util.* msg*.* context.* proc.wrapper
from core.util import signals, cmdutil, funcutil, tasks, linenc
from core.msg import msgabc, msgext, msgftr, msgpipe
from core.msgc import mc


class _PipeInLineCommand:

    def __init__(self, cmdline: str, catcher: typing.Optional[msgabc.Catcher] = None, force: bool = False):
        self.cmdline, self.catcher, self.force = cmdline, catcher, force


class _PipeInLineHandler(msgabc.Handler):

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: streams.StreamWriter):
        self._mailer, self._pipe = mailer, pipe

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        self._mailer.post(self, PipeInLineService.PIPE_CLOSE, self._pipe)

    async def handle(self, message):
        command = message.data()
        if command.catcher:
            self._mailer.register(command.catcher)
        try:
            self._pipe.write(command.cmdline.encode())
            self._pipe.write(b'\n')
            response = await command.catcher.get() if command.catcher else None
            self._mailer.post(self, PipeInLineService.RESPONSE, response, message)
        except asyncio.TimeoutError as e:
            logging.warning('Timeout on cmdline into pipein.')
            self._mailer.post(self, PipeInLineService.EXCEPTION, e, message)
        except Exception as e:
            logging.error('Failed pass cmdline into pipein: %s', repr(e))
            self._mailer.post(self, PipeInLineService.EXCEPTION, e, message)
        return None


class PipeInLineService(msgabc.Subscriber):
    REQUEST = 'PipeInLineService.Request'
    RESPONSE, EXCEPTION = 'PipeInLineService.Response', 'PipeInLineService.Exception'
    SERVICE_START, SERVICE_END = 'PipeInLineService.Start', 'PipeInLineService.End'
    PIPE_NEW, PIPE_CLOSE = 'PipeInLineService.PipeNew', 'PipeInLineService.PipeClose'
    FILTER_REQUEST, FILTER_PIPE_NEW = msgftr.NameIs(REQUEST), msgftr.NameIs(PIPE_NEW)

    @staticmethod
    async def request(mailer: msgabc.MulticastMailer, source: typing.Any, cmdline: str,
                      catcher: typing.Optional[msgabc.Catcher] = None, force: bool = False) -> typing.Any:
        response = await msgext.SynchronousMessenger(mailer).request(
            source, PipeInLineService.REQUEST,
            _PipeInLineCommand(cmdline, catcher, force))
        return response.data()

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: typing.Optional[streams.StreamWriter] = None):
        self._mailer, self._enabled = mailer, False
        self._msg_filter = msgftr.Or(
            PipeInLineService.FILTER_REQUEST,
            mc.ServerProcess.FILTER_STATE_STARTED,
            mc.ServerProcess.FILTER_STATES_DOWN)
        if pipe is None:
            self._msg_filter = msgftr.Or(self._msg_filter, PipeInLineService.FILTER_PIPE_NEW)
            self._persistent, self._handler = True, None
        else:
            self._persistent, self._handler = False, _PipeInLineHandler(mailer, pipe)
        mailer.post(self, PipeInLineService.SERVICE_START, self)
        mailer.register(self)

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    async def handle(self, message):
        if mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            self._enabled = True
            return None
        if PipeInLineService.FILTER_PIPE_NEW.accepts(message):
            assert self._handler is None
            self._handler = _PipeInLineHandler(self._mailer, message.data())
            return None
        if mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._enabled = False
            if self._handler is not None:
                await self._handler.close()
                self._handler = None
            if self._persistent:
                return None
            self._mailer.post(self, PipeInLineService.SERVICE_END, self)
            return True
        if not (self._enabled or message.data().force) or self._handler is None:
            self._mailer.post(self, PipeInLineService.RESPONSE, False, message)
            return None
        return await self._handler.handle(message)


class ServerProcess:

    def __init__(self, mailer: msgabc.MulticastMailer, executable: str):
        self._mailer = mailer
        self._command = cmdutil.CommandLine(executable)
        self._out_decoder = linenc.DefaultLineDecoder()
        self._pipeinsvc, self._started_catcher = None, None
        self._process, self._env, self._cwd = None, None, None

    def append_arg(self, arg: str | int | float) -> ServerProcess:
        self._command.append(arg)
        return self

    def append_struct(self, struct: dict, joiner: str = None) -> ServerProcess:
        self._command.append_struct(struct, joiner)
        return self

    def use_pipeinsvc(self, pipeinsvc: PipeInLineService) -> ServerProcess:
        self._pipeinsvc = pipeinsvc
        return self

    def use_out_decoder(self, line_decoder: linenc.LineDecoder) -> ServerProcess:
        self._out_decoder = line_decoder
        return self

    def use_env(self, env: dict[str, str]) -> ServerProcess:
        self._env = env
        return self

    def use_cwd(self, cwd: str) -> ServerProcess:
        self._cwd = cwd
        return self

    def wait_for_started(self, msg_filter: msgabc.Filter, timeout: float) -> ServerProcess:
        self._started_catcher = msgext.SingleCatcher(msgftr.Or(
            mc.ServerProcess.FILTER_STATE_STOPPING, mc.ServerProcess.FILTER_STATES_DOWN, msg_filter), timeout)
        self._mailer.register(self._started_catcher)
        return self

    async def run(self):
        cmdline, stderr, stdout = self._command.build_str(), None, None
        try:
            self._mailer.post(self, mc.ServerProcess.STATE_START, cmdline)
            cmdlist = self._command.build_list()
            self._process = await asyncio.create_subprocess_exec(
                cmdlist[0], *cmdlist[1:], stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env=self._env, cwd=self._cwd)
            pid, rc = self._process.pid, self._process.returncode
            if rc is not None:  # I don't think this can happen but to be sure
                raise Exception(f'PID {pid} exit after START, rc={rc}')
            stderr = msgpipe.PipeOutLineProducer(
                self._mailer, self, mc.ServerProcess.STDERR_LINE, self._process.stderr, self._out_decoder)
            stdout = msgpipe.PipeOutLineProducer(
                self._mailer, self, mc.ServerProcess.STDOUT_LINE, self._process.stdout, self._out_decoder)
            self._mailer.post(self, PipeInLineService.PIPE_NEW, self._process.stdin)
            if not self._pipeinsvc:
                PipeInLineService(self._mailer, self._process.stdin)
            self._mailer.post(self, mc.ServerProcess.STATE_STARTING, self._process)
            if self._started_catcher:
                tasks.task_fork(self._wait_for_started(), f'wait_for_started({pid})')
            else:
                self._mailer.post(self, mc.ServerProcess.STATE_STARTED, self._process)
            rc = await self._process.wait()
            if rc != 0:
                raise Exception(f'PID {pid} non-zero exit after STARTED, rc={rc}')
            self._mailer.post(self, mc.ServerProcess.STATE_STOPPED, self._process)
        except Exception as e:
            self._mailer.post(self, mc.ServerProcess.STATE_EXCEPTION, e)
            logging.error('Exception executing "%s" > %s', cmdline, repr(e))
        finally:
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)
            # PipeInLineService closes itself via PROCESS_ENDED message
            self._process = None

    async def _wait_for_started(self):
        try:
            if self._process.returncode is not None:  # One last check before wait
                return
            message = await self._started_catcher.get()
            if mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
                return
            if mc.ServerProcess.FILTER_STATE_STOPPING.accepts(message):
                return
            self._mailer.post(self, mc.ServerProcess.STATE_STARTED, self._process)
        except asyncio.TimeoutError:
            pid, rc = self._process.pid, self._process.returncode
            if rc is not None:
                return
            # Zombie process
            logging.error('Timeout on PID %s waiting for STARTED, killing now', pid)
            await signals.silently_kill_tree(pid)
