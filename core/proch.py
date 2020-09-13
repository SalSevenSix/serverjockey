import logging
import asyncio
from core import msgsvc, msgext, msgftr, util


class PipeOutLineProducer:

    def __init__(self, mailer, process, name, pipe):
        self.mailer = mailer
        self.process = process
        self.name = name
        self.pipe = pipe
        self.publisher = msgext.Publisher(mailer, self)

    async def close(self):
        # pipe has no close, so just stop the publisher
        await self.publisher.stop()

    async def next_message(self):
        line = await self.pipe.readline()  # blocking
        if line is None or line == b'':
            return None
        return msgsvc.Message(self.process, self.name, line.decode().strip())


class PipeInLineService:

    REQUEST = 'PipeInLineService.PipeInRequest'
    RESPONSE = 'PipeInLineService.PipeInResponse'
    EXCEPTION = 'PipeInLineService.PipeInException'
    SERVICE_START = 'PipeInLineService.Start'
    SERVICE_END = 'PipeInLineService.End'
    PIPE_USE = 'PipeInLineService.PipeUse'
    PIPE_CLOSE = 'PipeInLineService.PipeClose'

    class Command:
        def __init__(self, cmdline, catcher=None, force=False):
            assert isinstance(cmdline, str)
            assert catcher is None or msgsvc.is_catcher(catcher)
            self.cmdline = cmdline
            self.catcher = catcher
            self.force = force

    class Handler:
        def __init__(self, mailer, pipe):
            self.mailer = mailer
            self.pipe = pipe
            self.mailer.post((self, PipeInLineService.PIPE_USE, pipe))

        def close(self):
            self.pipe.close()
            self.mailer.post((self, PipeInLineService.PIPE_CLOSE, self.pipe))

        async def handle(self, message):
            command = message.get_data()
            if command.catcher:
                self.mailer.register(command.catcher)
            try:
                self.pipe.write(command.cmdline.encode())
                self.pipe.write(b'\n')
                response = await command.catcher.get() if command.catcher else None  # blocking
                self.mailer.post((self, PipeInLineService.RESPONSE, response, message))
            except asyncio.exceptions.TimeoutError as e:
                logging.warning('Timeout on cmdline into pipein. raised: %s', e)
                self.mailer.post((self, PipeInLineService.EXCEPTION, e, message))
                # TODO still need to unregister catcher
            except Exception as e:
                logging.error('Failed pass cmdline into pipein. raised: %s', e)
                self.mailer.post((self, PipeInLineService.EXCEPTION, e, message))
                return e   # TODO need to consider cleanup or just return None instead
            return None

    @staticmethod
    async def request(mailer, source, cmdline, catcher=None, force=False):
        messenger = msgext.SynchronousMessenger(mailer)
        return await messenger.request(msgsvc.Message(
            source,
            PipeInLineService.REQUEST,
            PipeInLineService.Command(cmdline, catcher, force)))

    def __init__(self, mailer, pipe=None):
        self.mailer = mailer
        self.enabled = False
        if pipe is None:
            self.persistent = True
            self.handler = None
        else:
            self.persistent = False
            self.handler = PipeInLineService.Handler(mailer, pipe)
        self.msg_filter = msgftr.Or((
            Filter.PIPEINSVC_REQUEST,
            Filter.PROCESS_STATE_STARTED,
            Filter.PROCESS_STATE_DOWN))
        mailer.post((self, PipeInLineService.SERVICE_START, self))
        mailer.register(self)

    # TODO consider receiving the pipe via message
    def use_pipe(self, pipe):
        assert self.handler is None
        self.handler = PipeInLineService.Handler(self.mailer, pipe)

    def accepts(self, message):
        return self.msg_filter.accepts(message)

    async def handle(self, message):
        if Filter.PROCESS_STATE_STARTED.accepts(message):
            self.enabled = True
            return None
        if Filter.PROCESS_STATE_DOWN.accepts(message):
            self.enabled = False
            if self.handler is not None:
                self.handler.close()
                self.handler = None
            if self.persistent:
                return None
            self.mailer.post((self, PipeInLineService.SERVICE_END, self))
            return True
        if not (self.enabled or message.get_data().force) or self.handler is None:
            self.mailer.post((self, PipeInLineService.RESPONSE, False, message))
            return None
        return await self.handler.handle(message)


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

    def __init__(self, mailer, executable):
        assert msgsvc.is_multimailer(mailer)
        assert executable is not None
        self.mailer = mailer
        self.command = util.CommandLine(executable)
        self.pipeinsvc = None
        self.process = None
        self.started_catcher = None
        self.started_timeout = None

    def use_pipeinsvc(self, pipeinsvc):
        self.pipeinsvc = pipeinsvc
        return self

    def append_arg(self, arg):
        self.command.append_command(arg)
        return self

    def wait_for_started(self, catcher):
        self.started_catcher = catcher
        self.mailer.register(catcher)
        return self

    def terminate(self):
        self.process.terminate()
        self.mailer.post((self, ProcessHandler.STATE_TERMINATED, self.process))

    async def run(self):
        rc, cmdline, stderr, stdout = (9, self.command.build(), None, None)
        try:
            self.mailer.post((self, ProcessHandler.STATE_START, cmdline))
            cmdlist = self.command.build(output=list)
            self.process = await asyncio.create_subprocess_exec(
                cmdlist[0],
                *cmdlist[1:],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stderr = PipeOutLineProducer(self.mailer, self, ProcessHandler.STDERR_LINE, self.process.stderr)
            stdout = PipeOutLineProducer(self.mailer, self, ProcessHandler.STDOUT_LINE, self.process.stdout)
            if self.pipeinsvc:
                self.pipeinsvc.use_pipe(self.process.stdin)
            else:
                PipeInLineService(self.mailer, self.process.stdin)
            self.mailer.post((self, ProcessHandler.STATE_STARTING, self.process))
            if self.started_catcher is not None:
                await self.started_catcher.get()   # blocking
            self.mailer.post((self, ProcessHandler.STATE_STARTED, self.process))
            rc = await self.process.wait()   # blocking
            self.mailer.post((self, ProcessHandler.STATE_COMPLETE, self.process))
        except asyncio.exceptions.TimeoutError:
            logging.error('Timeout waiting for PROCESS_STARTED after %s seconds', self.started_timeout)
            self.mailer.post((self, ProcessHandler.STATE_TIMEOUT, self.process))
            self.terminate()
        except Exception as e:
            logging.error('Exception executing "%s" > %s', cmdline, repr(e))
            self.mailer.post((self, ProcessHandler.STATE_EXCEPTION, e))
        finally:
            if stdout:
                await stdout.close()
            if stderr:
                await stderr.close()
            # PipeInLineService closes itself via PROCESS_ENDED message
            self.process = None
        return rc


class Filter:
    PROCESS_STATE_STARTED = msgftr.NameIs(ProcessHandler.STATE_STARTED)
    PROCESS_STATE_ALL = msgftr.NameIn(ProcessHandler.STATES_ALL)
    PROCESS_STATE_UP = msgftr.NameIn(ProcessHandler.STATES_UP)
    PROCESS_STATE_DOWN = msgftr.NameIn(ProcessHandler.STATES_DOWN)
    STDERR_LINE = msgftr.NameIs(ProcessHandler.STDERR_LINE)
    STDOUT_LINE = msgftr.NameIs(ProcessHandler.STDOUT_LINE)
    PIPEINSVC_REQUEST = msgftr.NameIs(PipeInLineService.REQUEST)
