import abc
# ALLOW util.* msg*.* context.* http.*
from core.context import contextsvc
from core.http import httprsc


class Server(metaclass=abc.ABCMeta):

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    @abc.abstractmethod
    def __init__(self, context: contextsvc.Context):
        pass

    @abc.abstractmethod
    async def initialise(self):
        pass

    @abc.abstractmethod
    def resources(self, resource: httprsc.WebResource):
        pass

    @abc.abstractmethod
    async def run(self):
        pass

    @abc.abstractmethod
    async def stop(self):
        pass
