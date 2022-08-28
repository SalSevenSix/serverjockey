from __future__ import annotations
import logging
import typing
import asyncio
from asyncio import streams, subprocess
from core.util import cmdutil, util
from core.msg import msgabc, msgext, msgftr


class _PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str, pipe: streams.StreamReader):
        self._source = source
        self._name = name
        self._pipe = pipe
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await util.silently_cleanup(self._pipe)
        await util.silently_cleanup(self._publisher)

    async def next_message(self):
        line = None
        # noinspection PyBroadException
        try:
            line = await self._pipe.readline()
        except Exception:
            pass
        if line is None or line == b'':
            logging.debug('EOF read from PipeOut: ' + repr(self._pipe))
            return None
        return msgabc.Message(self._source, self._name, line.decode().strip())


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
        command = message.data()
        if command.catcher:
            self._mailer.register(command.catcher)
        try:
            self._pipe.write(command.cmdline.encode())
            self._pipe.write(b'\n')
            response = await command.catcher.get() if command.catcher else None
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
    FILTER_REQUEST = msgftr.NameIs(REQUEST)
    FILTER_PIPE_NEW = msgftr.NameIs(PIPE_NEW)

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
        return response.data()

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: typing.Optional[streams.StreamWriter] = None):
        self._mailer = mailer
        self._enabled = False
        self._msg_filter = msgftr.Or(
            PipeInLineService.FILTER_REQUEST,
            ServerProcess.FILTER_STATE_STARTED,
            ServerProcess.FILTER_STATE_DOWN)
        if pipe is None:
            self._msg_filter = msgftr.Or(self._msg_filter, PipeInLineService.FILTER_PIPE_NEW)
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
        if ServerProcess.FILTER_STATE_STARTED.accepts(message):
            self._enabled = True
            return None
        if PipeInLineService.FILTER_PIPE_NEW.accepts(message):
            assert self._handler is None
            self._handler = _PipeInLineHandler(self._mailer, message.data())
            return None
        if ServerProcess.FILTER_STATE_DOWN.accepts(message):
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
    STDERR_LINE = 'ServerProcess.StdErrLine'
    STDOUT_LINE = 'ServerProcess.StdOutLine'
    STATE_START = 'ServerProcess.StateStart'
    STATE_STARTING = 'ServerProcess.StateStarting'
    STATE_STARTED = 'ServerProcess.StateStarted'
    STATE_TIMEOUT = 'ServerProcess.StateTimeout'
    STATE_TERMINATED = 'ServerProcess.StateTerminate'
    STATE_EXCEPTION = 'ServerProcess.StateException'
    STATE_COMPLETE = 'ServerProcess.StateComplete'
    STATES_UP = (STATE_START, STATE_STARTING, STATE_STARTED, STATE_TIMEOUT)
    STATES_DOWN = (STATE_TERMINATED, STATE_EXCEPTION, STATE_COMPLETE)
    STATES_ALL = STATES_UP + STATES_DOWN

    FILTER_STDERR_LINE = msgftr.NameIs(STDERR_LINE)
    FILTER_STDOUT_LINE = msgftr.NameIs(STDOUT_LINE)
    FILTER_STATE_STARTED = msgftr.NameIs(STATE_STARTED)
    FILTER_STATE_ALL = msgftr.NameIn(STATES_ALL)
    FILTER_STATE_UP = msgftr.NameIn(STATES_UP)
    FILTER_STATE_DOWN = msgftr.NameIn(STATES_DOWN)

    def __init__(self, mailer: msgabc.MulticastMailer, executable: str):
        self._mailer = mailer
        self._command = cmdutil.CommandLine(executable)
        self._process = None
        self._pipeinsvc = None
        self._started_catcher = None

    def use_pipeinsvc(self, pipeinsvc: PipeInLineService) -> ServerProcess:
        self._pipeinsvc = pipeinsvc
        return self

    def append_arg(self, arg: typing.Any) -> ServerProcess:
        self._command.append_command(arg)
        return self

    def wait_for_started(self, catcher: msgabc.Catcher) -> ServerProcess:
        self._started_catcher = catcher
        self._mailer.register(catcher)
        return self

    async def run(self):
        cmdline, stderr, stdout = self._command.build_str(), None, None
        try:
            self._mailer.post(self, ServerProcess.STATE_START, cmdline)
            cmdlist = self._command.build_list()
            self._process = await asyncio.create_subprocess_exec(
                cmdlist[0], *cmdlist[1:],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stderr = _PipeOutLineProducer(self._mailer, self, ServerProcess.STDERR_LINE, self._process.stderr)
            stdout = _PipeOutLineProducer(self._mailer, self, ServerProcess.STDOUT_LINE, self._process.stdout)
            self._mailer.post(self, PipeInLineService.PIPE_NEW, self._process.stdin)
            if not self._pipeinsvc:
                PipeInLineService(self._mailer, self._process.stdin)
            self._mailer.post(self, ServerProcess.STATE_STARTING, self._process)
            if self._started_catcher is not None:
                await self._started_catcher.get()  # blocks throws TimeoutError
            rc = self._process.returncode
            if rc is not None:
                raise Exception('Process {} exit after STARTING, rc={}'.format(self._process, rc))
            self._mailer.post(self, ServerProcess.STATE_STARTED, self._process)
            rc = await self._process.wait()  # blocking
            if rc != 0:
                raise Exception('Process {} non-zero exit after STARTED, rc={}'.format(self._process, rc))
            self._mailer.post(self, ServerProcess.STATE_COMPLETE, self._process)
        except asyncio.TimeoutError:
            rc = self._process.returncode
            if rc is None:  # Zombie process
                logging.error('Timeout waiting for STARTED but process still running, terminating now')
                self._mailer.post(self, ServerProcess.STATE_TIMEOUT, self._process)
                self._process.terminate()
                self._mailer.post(self, ServerProcess.STATE_TERMINATED, self._process)
            else:  # It's dead Jim
                logging.error('Timeout waiting for STARTED because process exit rc=' + str(rc))
                self._mailer.post(self, ServerProcess.STATE_EXCEPTION,
                                  Exception('Process {} exit during STARTING, rc={}'.format(self._process, rc)))
        except Exception as e:
            logging.error('Exception executing "%s" > %s', cmdline, repr(e))
            self._mailer.post(self, ServerProcess.STATE_EXCEPTION, e)
        finally:
            await util.silently_cleanup(stdout)
            await util.silently_cleanup(stderr)
            # PipeInLineService closes itself via PROCESS_ENDED message
            self._process = None


class JobProcess(msgabc.AbcSubscriber):
    STDERR_LINE = 'JobProcess.StdErrLine'
    STDOUT_LINE = 'JobProcess.StdOutLine'
    START = 'JobProcess.Start'
    STATE_STARTED = 'JobProcess.StateStarted'
    STATE_EXCEPTION = 'JobProcess.StateException'
    STATE_COMPLETE = 'JobProcess.StateComplete'
    JOB_DONE = (STATE_EXCEPTION, STATE_COMPLETE)
    FILTER_STDERR_LINE = msgftr.NameIs(STDERR_LINE)
    FILTER_STDOUT_LINE = msgftr.NameIs(STDOUT_LINE)
    FILTER_JOB_DONE = msgftr.NameIn(JOB_DONE)

    @staticmethod
    async def start_job(
            mailer: msgabc.MulticastMailer,
            source: typing.Any,
            command: typing.Union[str, typing.Collection[str]]) -> typing.Union[subprocess.Process, Exception]:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, JobProcess.START, command)
        return response.data()

    @staticmethod
    async def run_job(
            mailer: msgabc.MulticastMailer,
            source: typing.Any,
            command: typing.Union[str, typing.Collection[str]]) -> typing.Union[subprocess.Process, Exception]:
        messenger = msgext.SynchronousMessenger(mailer, catcher=msgext.SingleCatcher(JobProcess.FILTER_JOB_DONE))
        response = await messenger.request(source, JobProcess.START, command)
        return response.data()

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.NameIs(JobProcess.START))
        self._mailer = mailer

    async def handle(self, message):
        source, command = message.source(), message.data()
        if isinstance(command, dict):
            command = util.get('command', command, util.get('script', command))
        if not (isinstance(command, str) or util.iterable(command)):
            self._mailer.post(source, JobProcess.STATE_EXCEPTION, Exception('Invalid job request'), message)
            return None
        stderr, stdout, replied = None, None, False
        try:
            if isinstance(command, str):
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            else:
                process = await asyncio.create_subprocess_exec(
                    command[0], *command[1:],
                    stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stderr = _PipeOutLineProducer(self._mailer, source, JobProcess.STDERR_LINE, process.stderr)
            stdout = _PipeOutLineProducer(self._mailer, source, JobProcess.STDOUT_LINE, process.stdout)
            replied = self._mailer.post(source, JobProcess.STATE_STARTED, process, message)
            rc = await process.wait()
            if rc != 0:
                raise Exception('Process {} non-zero exit after STARTED, rc={}'.format(process, rc))
            self._mailer.post(source, JobProcess.STATE_COMPLETE, process)
        except Exception as e:
            self._mailer.post(source, JobProcess.STATE_EXCEPTION, e, None if replied else message)
        finally:
            await util.silently_cleanup(stdout)
            await util.silently_cleanup(stderr)
        return None
