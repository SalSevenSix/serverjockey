import abc
import re
# ALLOW util.* msg.* context.*


class LineDecoder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, line: bytes) -> str:
        pass


class DefaultLineDecoder(LineDecoder):

    def decode(self, line: bytes) -> str:
        return line.decode().strip()


class PtyLineDecoder(LineDecoder):
    _ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def decode(self, line: bytes) -> str:
        result = line.decode().strip()
        result = PtyLineDecoder._ANSI_ESCAPE.sub('', result)
        result = result.replace('\x1B', '').replace('\x07', ' ')
        return result
