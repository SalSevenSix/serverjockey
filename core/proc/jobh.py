import typing
import asyncio
from asyncio import subprocess
from core.proc import procabc
from core.util import util, funcutil
from core.msg import msgabc, msgext, msgftr


class JobProcess(msgabc.AbcSubscriber):
    STDERR_LINE = 'JobProcess.StdErrLine'
    STDOUT_LINE = 'JobProcess.StdOutLine'
    START = 'JobProcess.Start'

    STATE_STARTED = 'JobProcess.StateStarted'
    STATE_COMPLETE = 'JobProcess.StateComplete'
    STATE_EXCEPTION = 'JobProcess.StateException'

    FILTER_STDERR_LINE = msgftr.NameIs(STDERR_LINE)
    FILTER_STDOUT_LINE = msgftr.NameIs(STDOUT_LINE)
    FILTER_JOB_DONE = msgftr.NameIn((STATE_EXCEPTION, STATE_COMPLETE))

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
            stderr = procabc.PipeOutLineProducer(self._mailer, source, JobProcess.STDERR_LINE, process.stderr)
            stdout = procabc.PipeOutLineProducer(self._mailer, source, JobProcess.STDOUT_LINE, process.stdout)
            replied = self._mailer.post(source, JobProcess.STATE_STARTED, process, message)
            rc = await process.wait()
            if rc != 0:
                raise Exception('Process {} non-zero exit after STARTED, rc={}'.format(process, rc))
            self._mailer.post(source, JobProcess.STATE_COMPLETE, process)
        except Exception as e:
            self._mailer.post(source, JobProcess.STATE_EXCEPTION, e, None if replied else message)
        finally:
            await funcutil.silently_cleanup(stdout)
            await funcutil.silently_cleanup(stderr)
        return None
