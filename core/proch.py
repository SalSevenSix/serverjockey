from __future__ import annotations
import logging
import asyncio
import typing
from asyncio import streams
from core import msgabc, msgext, msgftr, cmdutil, util


class _PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, process: ProcessHandler, name: str, pipe: streams.StreamReader):
        self._process = process
        self._name = name
        self._pipe = pipe
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await util.silently_cleanup(self._pipe)
        await util.silently_cleanup(self._publisher)

    async def next_message(self):
        line = None
        try:
            line = await self._pipe.readline()   # blocking
        except Exception:
            pass
        if line is None or line == b'':
            logging.debug('EOF read from PipeOut: ' + repr(self._pipe))
            return None
        return msgabc.Message(self._process, self._name, line.decode().strip())


class _PipeInLineCommand:

    def __init__(self, cmdline: str, catcher: typing.Optional[msgabc.Catcher] = None, force: bool = False):
        self.cmdline = cmdline
        self.catcher = catcher
        self.force = force


class _PipeInLineHandler(msgabc.Handler):

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: streams.StreamWriter):
        self._mailer = mailer
        self._pipe = pipe

    async def close(self):
        await util.silently_cleanup(self._pipe)
        self._mailer.post(self, PipeInLineService.PIPE_CLOSE, self._pipe)

    async def handle(self, message):
        command = message.get_data()
        if command.catcher:
            self._mailer.register(command.catcher)
        try:
            self._pipe.write(command.cmdline.encode())
            self._pipe.write(b'\n')
            response = await command.catcher.get() if command.catcher else None  # blocking
            self._mailer.post(self, PipeInLineService.RESPONSE, response, message)
        except asyncio.TimeoutError as e:
            logging.warning('Timeout on cmdline into pipein. raised: ' + repr(e))
            self._mailer.post(self, PipeInLineService.EXCEPTION, e, message)
        except Exception as e:
            logging.error('Failed pass cmdline into pipein. raised: ' + repr(e))
            self._mailer.post(self, PipeInLineService.EXCEPTION, e, message)
        return None


class PipeInLineService(msgabc.Subscriber):
    REQUEST = 'PipeInLineService.Request'
    RESPONSE = 'PipeInLineService.Response'
    EXCEPTION = 'PipeInLineService.Exception'
    SERVICE_START = 'PipeInLineService.Start'
    SERVICE_END = 'PipeInLineService.End'
    PIPE_NEW = 'PipeInLineService.PipeNew'
    PIPE_CLOSE = 'PipeInLineService.PipeClose'

    @staticmethod
    async def request(
            mailer: msgabc.MulticastMailer,
            source: typing.Any,
            cmdline: str,
            catcher: typing.Optional[msgabc.Catcher] = None,
            force: bool = False) -> typing.Any:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(
            source, PipeInLineService.REQUEST,
            _PipeInLineCommand(cmdline, catcher, force))
        return response.get_data()

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: typing.Optional[streams.StreamWriter] = None):
        self._mailer = mailer
        self._enabled = False
        self._msg_filter = msgftr.Or(
            Filter.PIPEINSVC_REQUEST,
            Filter.PROCESS_STATE_STARTED,
            Filter.PROCESS_STATE_DOWN)
        if pipe is None:
            self._msg_filter = msgftr.Or(self._msg_filter, Filter.PIPEINSVC_PIPE_NEW)
            self._persistent = True
            self._handler = None
        else:
            self._persistent = False
            self._handler = _PipeInLineHandler(mailer, pipe)
        mailer.post(self, PipeInLineService.SERVICE_START, self)
        mailer.register(self)

    def accepts(self, message):
        return self._msg_filter.accepts(message)

    async def handle(self, message):
        if Filter.PROCESS_STATE_STARTED.accepts(message):
            self._enabled = True
            return None
        if Filter.PIPEINSVC_PIPE_NEW.accepts(message):
            assert self._handler is None
            self._handler = _PipeInLineHandler(self._mailer, message.get_data())
            return None
        if Filter.PROCESS_STATE_DOWN.accepts(message):
            self._enabled = False
            if self._handler is not None:
                await self._handler.close()
                self._handler = None
            if self._persistent:
                return None
            self._mailer.post(self, PipeInLineService.SERVICE_END, self)
            return True
        if not (self._enabled or message.get_data().force) or self._handler is None:
            self._mailer.post(self, PipeInLineService.RESPONSE, False, message)
            return None
        return await self._handler.handle(message)


class ProcessHandler:
    STDERR_LINE = 'ProcessHandler.StdErrLine'
    STDOUT_LINE = 'ProcessHandler.StdOutLine'
    STATE_START = 'ProcessHandler.ProcessStart'
    STATE_STARTING = 'ProcessHandler.ProcessStarting'
    STATE_STARTED = 'ProcessHandler.ProcessStarted'
    STATE_TIMEOUT = 'ProcessHandler.ProcessTimeout'
    STATE_TERMINATED = 'ProcessHandler.ProcessTerminate'
    STATE_EXCEPTION = 'ProcessHandler.ProcessException'
    STATE_COMPLETE = 'ProcessHandler.ProcessComplete'
    STATES_UP = (STATE_START, STATE_STARTING, STATE_STARTED, STATE_TIMEOUT)
    STATES_DOWN = (STATE_TERMINATED, STATE_EXCEPTION, STATE_COMPLETE)
    STATES_ALL = STATES_UP + STATES_DOWN

    def __init__(self, mailer: msgabc.MulticastMailer, executable: str):
        self._mailer = mailer
        self._command = cmdutil.CommandLine(executable)
        self._process = None
        self._pipeinsvc = None
        self._started_catcher = None

    def use_pipeinsvc(self, pipeinsvc: PipeInLineService) -> ProcessHandler:
        self._pipeinsvc = pipeinsvc
        return self

    def append_arg(self, arg: typing.Any) -> ProcessHandler:
        self._command.append_command(arg)
        return self

    def wait_for_started(self, catcher: msgabc.Catcher) -> ProcessHandler:
        self._started_catcher = catcher
        self._mailer.register(catcher)
        return self

    def terminate(self):
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        self._mailer.post(self, ProcessHandler.STATE_TERMINATED, self._process)

    async def run(self):
        cmdline, stderr, stdout = self._command.build_str(), None, None
        try:
            self._mailer.post(self, ProcessHandler.STATE_START, cmdline)
            cmdlist = self._command.build_list()
            self._process = await asyncio.create_subprocess_exec(
                cmdlist[0], *cmdlist[1:],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stderr = _PipeOutLineProducer(self._mailer, self, ProcessHandler.STDERR_LINE, self._process.stderr)
            stdout = _PipeOutLineProducer(self._mailer, self, ProcessHandler.STDOUT_LINE, self._process.stdout)
            self._mailer.post(self, PipeInLineService.PIPE_NEW, self._process.stdin)
            if not self._pipeinsvc:
                PipeInLineService(self._mailer, self._process.stdin)
            self._mailer.post(self, ProcessHandler.STATE_STARTING, self._process)
            if self._started_catcher is not None:
                await self._started_catcher.get()   # blocking
            rc = self._process.returncode
            if rc is not None:
                raise Exception('Process {} exit after STARTING, rc={}'.format(self._process, rc))
            self._mailer.post(self, ProcessHandler.STATE_STARTED, self._process)
            rc = await self._process.wait()   # blocking
            if rc != 0:
                raise Exception('Process {} non-zero exit after STARTED, rc={}'.format(self._process, rc))
            self._mailer.post(self, ProcessHandler.STATE_COMPLETE, self._process)
        except asyncio.TimeoutError:
            rc = self._process.returncode
            if rc is not None:   # It's dead Jim
                logging.error('Timeout waiting for STARTED because process exit rc=' + str(rc))
                self._mailer.post(self, ProcessHandler.STATE_EXCEPTION,
                                  Exception('Process {} exit during STARTING, rc={}'.format(self._process, rc)))
            else:
                logging.error('Timeout waiting for STARTED but process still running, terminating now')
                self._mailer.post(self, ProcessHandler.STATE_TIMEOUT, self._process)
        except Exception as e:
            logging.error('Exception executing "%s" > %s', cmdline, repr(e))
            self._mailer.post(self, ProcessHandler.STATE_EXCEPTION, e)
        finally:
            await util.silently_cleanup(stdout)
            await util.silently_cleanup(stderr)
            # PipeInLineService closes itself via PROCESS_ENDED message
            self._process = None


class Filter:
    PROCESS_STATE_STARTED = msgftr.NameIs(ProcessHandler.STATE_STARTED)
    PROCESS_STATE_ALL = msgftr.NameIn(ProcessHandler.STATES_ALL)
    PROCESS_STATE_UP = msgftr.NameIn(ProcessHandler.STATES_UP)
    PROCESS_STATE_DOWN = msgftr.NameIn(ProcessHandler.STATES_DOWN)
    STDERR_LINE = msgftr.NameIs(ProcessHandler.STDERR_LINE)
    STDOUT_LINE = msgftr.NameIs(ProcessHandler.STDOUT_LINE)
    PIPEINSVC_REQUEST = msgftr.NameIs(PipeInLineService.REQUEST)
    PIPEINSVC_PIPE_NEW = msgftr.NameIs(PipeInLineService.PIPE_NEW)
