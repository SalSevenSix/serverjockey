import re
# ALLOW util.* msg.msgabc
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

    def __init__(self, msg_filter: msgabc.Filter):
        self._msg_filter = msg_filter

    def accepts(self, message):
        return not self._msg_filter.accepts(message)


class And(msgabc.Filter):

    def __init__(self, *msg_filters: msgabc.Filter):
        self._msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in self._msg_filters:
            if not msg_filter.accepts(message):
                return False
        return True


class Or(msgabc.Filter):

    def __init__(self, *msg_filters: msgabc.Filter):
        self._msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in self._msg_filters:
            if msg_filter.accepts(message):
                return True
        return False


class SourceIs(msgabc.Filter):

    def __init__(self, source_object):
        self._source_object = source_object

    def accepts(self, message):
        return self._source_object is message.source()


class ReplyToIs(msgabc.Filter):

    def __init__(self, reply_to: msgabc.Message):
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


class HasData(msgabc.Filter):

    def accepts(self, message):
        return bool(message.data())


class DataIn(msgabc.Filter):

    def __init__(self, values):
        self._values = values

    def accepts(self, message):
        return message.data() in self._values


class DataEquals(msgabc.Filter):

    def __init__(self, data):
        self._data = data

    def accepts(self, message):
        return self._data == message.data()


class DataStrStartsWith(msgabc.Filter):

    def __init__(self, value: str, invert: bool = False):
        self._value, self._invert = value, invert

    def accepts(self, message):
        data = message.data()
        if not isinstance(data, str):
            return False
        return self._value.startswith(data) if self._invert else data.startswith(self._value)


class DataStrContains(msgabc.Filter):

    def __init__(self, value: str, ignore_case: bool = False):
        self._value = value.lower() if ignore_case else value
        self._ignore_case = ignore_case

    def accepts(self, message):
        data = message.data()
        if not isinstance(data, str):
            return False
        if self._ignore_case:
            data = data.lower()
        return data.find(self._value) != -1


class DataMatches(msgabc.Filter):

    def __init__(self, regex: str | re.Pattern):
        self._pattern = regex if isinstance(regex, re.Pattern) else re.compile(regex)

    def accepts(self, message):
        return self._pattern.match(str(message.data())) is not None
