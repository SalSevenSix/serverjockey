import abc
# ALLOW const.* util.* msg.* context.*


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
