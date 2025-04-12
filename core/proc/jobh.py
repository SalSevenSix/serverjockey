import typing
import asyncio
from asyncio import subprocess, streams
# ALLOW util.* msg*.* context.* proc.wrapper
from core.util import util, idutil, funcutil, io, linenc
from core.msg import msgabc, msgext, msgftr, msgpipe
from core.context import contextsvc
from core.proc import wrapper


class JobPipeInLineService(msgabc.AbcSubscriber):
    REQUEST = 'JobPipeInLineService.Request'
    RESPONSE, EXCEPTION = 'JobPipeInLineService.Response', 'JobPipeInLineService.Exception'
    CLOSE = 'JobPipeInLineService.Close'

    @staticmethod
    async def request(mailer: msgabc.MulticastMailer, source: typing.Any, cmdline: str) -> typing.Any:
        messenger = msgext.SynchronousMessenger(mailer, timeout=2.0)
        response = await messenger.request(source, JobPipeInLineService.REQUEST, cmdline)
        return response.data()

    def __init__(self, mailer: msgabc.MulticastMailer, pipe: streams.StreamWriter):
        super().__init__(msgftr.NameIn((JobPipeInLineService.REQUEST, JobPipeInLineService.CLOSE)))
        self._mailer, self._pipe = mailer, pipe
        mailer.register(self)

    async def close(self):
        self._mailer.post(self, JobPipeInLineService.CLOSE)
        await funcutil.silently_cleanup(self._pipe)

    def handle(self, message):
        if message.name() is JobPipeInLineService.CLOSE:
            return True
        try:
            self._pipe.write(message.data().encode())
            self._pipe.write(b'\n')
            self._mailer.post(self, JobPipeInLineService.RESPONSE, None, message)
        except Exception as e:
            self._mailer.post(self, JobPipeInLineService.EXCEPTION, e, message)
        return None


class JobProcess(msgabc.AbcSubscriber):
    REQUEST = 'JobProcess.Request'
    STATE_STARTED = 'JobProcess.Started'
    STATE_COMPLETE = 'JobProcess.Complete'
    STATE_EXCEPTION = 'JobProcess.Exception'
    FILTER_STARTED = msgftr.NameIs(STATE_STARTED)
    FILTER_DONE = msgftr.NameIn((STATE_EXCEPTION, STATE_COMPLETE))
    STDOUT_LINE, STDERR_LINE = 'JobProcess.StdOutLine', 'JobProcess.StdErrLine'
    FILTER_STDOUT_LINE, FILTER_STDERR_LINE = msgftr.NameIs(STDOUT_LINE), msgftr.NameIs(STDERR_LINE)
    FILTER_ALL_LINES = msgftr.Or(FILTER_STDOUT_LINE, FILTER_STDERR_LINE)

    @staticmethod
    async def run_job(
            mailer: msgabc.MulticastMailer, source: typing.Any,
            command: typing.Union[str, dict, typing.Collection[str]]) -> typing.Union[subprocess.Process, Exception]:
        catcher = msgext.SingleCatcher(msgftr.And(msgftr.SourceIs(source), JobProcess.FILTER_DONE))
        messenger = msgext.SynchronousMessenger(mailer, catcher=catcher)
        response = await messenger.request(source, JobProcess.REQUEST, command)
        return response.data()

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.NameIs(JobProcess.REQUEST))
        self._mailer = context

    async def handle(self, message):
        stdin, stderr, stdout, replied = None, None, None, False
        command = _CommandHelper(self._mailer, message)
        try:
            await command.prepare()
            if command.is_script():
                process = await asyncio.create_subprocess_shell(
                    command.command(),
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            else:
                process = await asyncio.create_subprocess_exec(
                    command.command()[0], *command.command()[1:],
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stderr = msgpipe.PipeOutLineProducer(
                self._mailer, command.source(), JobProcess.STDERR_LINE, process.stderr, command.decoder())
            stdout = msgpipe.PipeOutLineProducer(
                self._mailer, command.source(), JobProcess.STDOUT_LINE, process.stdout, command.decoder())
            stdin = JobPipeInLineService(self._mailer, process.stdin)
            replied = self._mailer.post(command.source(), JobProcess.STATE_STARTED, process, message)
            rc = await process.wait()
            if rc != 0:
                raise Exception(f'Process {process} non-zero exit after STARTED, rc={rc}')
            self._mailer.post(command.source(), JobProcess.STATE_COMPLETE, process)
        except Exception as e:
            self._mailer.post(command.source(), JobProcess.STATE_EXCEPTION, e, None if replied else message)
        finally:
            await funcutil.silently_cleanup(stdin)
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)
            await funcutil.silently_cleanup(command)
        return None


class _CommandHelper:

    def __init__(self, context: contextsvc.Context, message: msgabc.Message):
        self._python, self._tempdir = context.config('python'), context.config('tempdir')
        self._source, self._command = message.source(), message.data()
        self._work_dir, self._pty = None, False
        if isinstance(self._command, dict):
            self._pty = util.get('pty', self._command, False)
            self._command = util.get('command', self._command)

    async def prepare(self):
        if not self._command or not isinstance(self._command, (str, list, tuple)):
            raise Exception('Invalid job request')
        if not self._pty:
            return
        self._work_dir = self._tempdir + '/' + idutil.generate_id()
        await io.create_directory(self._work_dir)
        command = [self._python, await wrapper.write_wrapper(self._work_dir)]
        if isinstance(self._command, str):
            command.extend(['/bin/bash', self._work_dir + '/job.sh'])
            await io.write_file(command[3], self._command)
        else:
            command.extend(self._command)
        self._command = tuple(command)

    def source(self) -> typing.Any:
        return self._source

    def is_script(self) -> bool:
        return isinstance(self._command, str)

    def command(self) -> typing.Union[str, typing.Collection[str]]:
        return self._command

    def decoder(self) -> linenc.LineDecoder:
        return linenc.PtyLineDecoder() if self._pty else linenc.DefaultLineDecoder()

    async def cleanup(self):
        await io.delete_directory(self._work_dir)
