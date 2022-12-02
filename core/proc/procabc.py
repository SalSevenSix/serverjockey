import abc
import logging
import typing
from asyncio import streams
from core.util import funcutil, io, pkg
from core.msg import msgabc, msgext


async def unpack_wrapper(path: str):
    filename = path + '/wrapper.py'
    data = await pkg.pkg_load('core.proc', 'wrapper.py')
    await io.write_file(filename, data)
    return filename


class LineDecoder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, line: bytes) -> str:
        pass


class DefaultLineDecoder(LineDecoder):

    def decode(self, line: bytes) -> str:
        return line.decode().strip()


class PtyLineDecoder(LineDecoder):

    def decode(self, line: bytes) -> str:
        result = line.decode().strip()
        result = result.replace('\x1b[37m', '')  # TODO need a more generic cleanup
        result = result.replace('\x1b[31m', '')
        result = result.replace('\x1b[6n', '')
        return result


class PipeOutLineProducer(msgabc.Producer):

    def __init__(self, mailer: msgabc.Mailer, source: typing.Any, name: str,
                 pipe: streams.StreamReader, decoder: LineDecoder = DefaultLineDecoder()):
        self._source = source
        self._name = name
        self._pipe = pipe
        self._decoder = decoder
        self._publisher = msgext.Publisher(mailer, self)

    async def close(self):
        await funcutil.silently_cleanup(self._pipe)
        await funcutil.silently_cleanup(self._publisher)

    async def next_message(self):
        # noinspection PyBroadException
        try:
            line = await self._pipe.readline()
            if line is None or line == b'':
                logging.debug('EOF read from PipeOut: ' + repr(self._pipe))
                return None
            return msgabc.Message(self._source, self._name, self._decoder.decode(line))
        except Exception as e:
            logging.error('Pipe read line failed: ' + repr(e))
        return None
