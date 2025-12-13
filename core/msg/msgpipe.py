import logging
import typing
import asyncio
from asyncio import streams
# ALLOW util.* msg*.* context.*
from core.util import funcutil, io, linenc, tasks
from core.msg import msgabc, msgext


class PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str,
                 pipe: streams.StreamReader, decoder: linenc.LineDecoder = linenc.DefaultLineDecoder()):
        self._source, self._name, self._pipe, self._decoder = source, name, pipe, decoder
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        await funcutil.silently_cleanup(self._publisher)

    async def next_message(self):
        try:
            line = await self._pipe.readline()
            if io.end_of_stream(line):
                logging.debug('EOF read from PipeOut: %s', repr(self._pipe))
                return None
            return msgabc.Message(self._source, self._name, self._decoder.decode(line))
        except Exception as e:
            logging.error('Pipe read line failed: %s', repr(e))
        return None


class TailPublisher:

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str, path: str):
        self._mailer, self._source, self._name, self._path = mailer, source, name, path
        self._task, self._stdout = None, None
        self._process: asyncio.subprocess.Process | None = None

    async def start(self) -> bool:
        try:
            self._process = await asyncio.create_subprocess_exec(
                'tail', '-f', self._path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            self._stdout = PipeOutLineProducer(self._mailer, self._source, self._name, self._process.stdout)
            self._task = tasks.task_start(self._run(), 'TailPublisher(' + self._path + ')')
            return True
        except Exception as e:
            logging.warning('Error starting tail -f %s %s', self._path, repr(e))
        return False

    async def _run(self):
        try:
            rc = await self._process.wait()
            logging.debug('tail -f %s exit code: %s', self._path, rc)
        except Exception as e:
            logging.warning('Error waiting tail -f %s %s', self._path, repr(e))
        finally:
            await funcutil.silently_cleanup(self._stdout)
            tasks.task_end(self._task)

    def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        try:
            self._process.terminate()
        except Exception as e:
            logging.warning('Error killing tail -f %s %s', self._path, repr(e))
