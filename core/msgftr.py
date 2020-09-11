import re


class AcceptAll:

    def accepts(self, message):
        return True


class AcceptNothing:

    def accepts(self, message):
        return False


class Not:

    def __init__(self, msg_filter):
        self.msg_filter = msg_filter

    def accepts(self, message):
        return not self.msg_filter.accepts(message)


class And:

    def __init__(self, msg_filters):
        self.msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in iter(self.msg_filters):
            if not msg_filter.accepts(message):
                return False
        return True


class Or:

    def __init__(self, msg_filters):
        self.msg_filters = tuple(msg_filters)

    def accepts(self, message):
        for msg_filter in iter(self.msg_filters):
            if msg_filter.accepts(message):
                return True
        return False


class SourceIs:

    def __init__(self, source_object):
        self.source_object = source_object

    def accepts(self, message):
        return self.source_object is message.get_source()


class SourceClassIs:

    def __init__(self, source_class):
        self.source_class = source_class

    def accepts(self, message):
        return self.source_class is type(message.get_source())


class ReplyToIs:

    def __init__(self, reply_to):
        self.reply_to = reply_to

    def accepts(self, message):
        return self.reply_to is message.get_reply_to()


class NameIs:

    def __init__(self, name):
        self.name = name

    def accepts(self, message):
        return self.name is message.get_name()


class NameIn:

    def __init__(self, names):
        self.names = names

    def accepts(self, message):
        return message.get_name() in self.names


class NameEquals:

    def __init__(self, name):
        self.name = name

    def accepts(self, message):
        return self.name == message.get_name()


class NameMatches:

    def __init__(self, regex):
        self.pattern = regex if regex is re.Pattern else re.compile(regex)

    def accepts(self, message):
        return self.pattern.match(str(message.get_name())) is not None


class DataEquals:

    def __init__(self, data):
        self.data = data

    def accepts(self, message):
        return self.data == message.get_data()


class DataStrContains:

    def __init__(self, value):
        self.value = value

    def accepts(self, message):
        return str(message.get_data()).find(self.value) != -1


class DataMatches:

    def __init__(self, regex):
        self.pattern = regex if regex is re.Pattern else re.compile(regex)

    def accepts(self, message):
        return self.pattern.match(str(message.get_data())) is not None
