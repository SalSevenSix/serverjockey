import re
from core.msg import msgabc


class AcceptAll(msgabc.Filter):

    def accepts(self, message):
        return True


class AcceptNothing(msgabc.Filter):

    def accepts(self, message):
        return False


class IsStop(msgabc.Filter):

    def accepts(self, message):
        return message is msgabc.STOP


class Not(msgabc.Filter):

    def __init__(self, msg_filter):
        self._msg_filter = msg_filter

    def accepts(self, message):
        return not self._msg_filter.accepts(message)


class And(msgabc.Filter):

    def __init__(self, *msg_filters):
        self._msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in iter(self._msg_filters):
            if not msg_filter.accepts(message):
                return False
        return True


class Or(msgabc.Filter):

    def __init__(self, *msg_filters):
        self._msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in iter(self._msg_filters):
            if msg_filter.accepts(message):
                return True
        return False


class SourceIs(msgabc.Filter):

    def __init__(self, source_object):
        self._source_object = source_object

    def accepts(self, message):
        return self._source_object is message.source()


class SourceClassIs(msgabc.Filter):

    def __init__(self, source_class):
        self._source_class = source_class

    def accepts(self, message):
        return self._source_class is type(message.source())


class ReplyToIs(msgabc.Filter):

    def __init__(self, reply_to):
        self._reply_to = reply_to

    def accepts(self, message):
        return self._reply_to is message.reply_to()


class NameIs(msgabc.Filter):

    def __init__(self, name):
        self._name = name

    def accepts(self, message):
        return self._name is message.name()


class NameIn(msgabc.Filter):

    def __init__(self, names):
        self._names = names

    def accepts(self, message):
        return message.name() in self._names


class NameEquals(msgabc.Filter):

    def __init__(self, name):
        self._name = name

    def accepts(self, message):
        return self._name == message.name()


class DataEquals(msgabc.Filter):

    def __init__(self, data):
        self._data = data

    def accepts(self, message):
        return self._data == message.data()


class DataStrContains(msgabc.Filter):

    def __init__(self, value):
        self._value = value

    def accepts(self, message):
        return str(message.data()).find(self._value) != -1


class DataMatches(msgabc.Filter):

    def __init__(self, regex):
        self._pattern = regex if regex is re.Pattern else re.compile(regex)

    def accepts(self, message):
        return self._pattern.match(str(message.data())) is not None