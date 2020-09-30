from core import util, msgabc


class Noop(msgabc.Transformer):

    def transform(self, message):
        return message


class GetData(msgabc.Transformer):

    def transform(self, message):
        return message.get_data()


class DataAsDict(msgabc.Transformer):

    def transform(self, message):
        return util.obj_to_dict(message.get_data())


class ToString(msgabc.Transformer):

    def transform(self, message):
        line = [str(util.to_millis(message.get_created())),
                str(message.get_id()),
                str(message.get_name()).ljust(32),
                util.obj_to_str(message.get_data())]
        if message.has_reply_to():
            line.append('[' + self.transform(message.get_reply_to()) + ']')
        return ' '.join(line)


class ToJson(msgabc.Transformer):

    def transform(self, message):
        return util.obj_to_json(message)
