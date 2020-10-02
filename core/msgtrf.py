from core import msgabc, util


class Noop(msgabc.Transformer):

    def transform(self, message):
        return message


class GetData(msgabc.Transformer):

    def transform(self, message):
        return message.data()


class DataAsDict(msgabc.Transformer):

    def transform(self, message):
        return util.obj_to_dict(message.data())


class ToString(msgabc.Transformer):

    def transform(self, message):
        line = [str(util.to_millis(message.created())),
                str(message.identity()),
                str(message.name()).ljust(32),
                util.obj_to_str(message.data())]
        if message.has_reply_to():
            line.append('[' + self.transform(message.reply_to()) + ']')
        return ' '.join(line)


class ToJson(msgabc.Transformer):

    def transform(self, message):
        return util.obj_to_json(message)
