import abc
# ALLOW const.* util.* msg.* context.* http.*
from core.context import contextsvc
from core.http import httpabc


class Server(metaclass=abc.ABCMeta):

    # noinspection PyUnusedLocal
    @abc.abstractmethod
    def __init__(self, context: contextsvc.Context):
        pass

    @abc.abstractmethod
    async def initialise(self):
        pass

    @abc.abstractmethod
    def resources(self, resource: httpabc.Resource):
        pass

    @abc.abstractmethod
    async def run(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass
