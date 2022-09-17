import abc
import typing


class Aggregator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def aggregate(self, collection: typing.Collection) -> typing.Any:
        pass


class Noop(Aggregator):

    def aggregate(self, collection):
        return collection


class StrJoin(Aggregator):

    def __init__(self, delim: str = ''):
        self._delim = delim

    def aggregate(self, collection):
        return self._delim.join(collection)
