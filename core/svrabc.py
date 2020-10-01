import abc
from core import httpabc, contextsvc


class Server(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, context: contextsvc.Context):
        pass

    @abc.abstractmethod
    async def initialise(self):
        pass

    @abc.abstractmethod
    def resources(self, name: str) -> httpabc.Resource:
        pass

    @abc.abstractmethod
    async def run(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass
