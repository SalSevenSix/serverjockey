from core.util import util
from core.msg import msgabc


class Noop(msgabc.Transformer):

    def transform(self, message):
        return message


class GetData(msgabc.Transformer):

    def transform(self, message):
        return message.data()


class DataAsDict(msgabc.Transformer):

    def transform(self, message):
        return util.obj_to_dict(message.data())


class ToLogLine(msgabc.Transformer):

    def transform(self, message):
        return 'msg> ' + ToLogLine._transform(message, 40)

    @staticmethod
    def _transform(message, pad):
        line = [util.obj_to_str(message.source()).ljust(pad),
                str(message.name()).ljust(pad),
                util.obj_to_str(message.data()).ljust(pad)]
        reply_to = message.reply_to()
        if reply_to:
            line.append('[' + ToLogLine._transform(reply_to, 10) + ']')
        return ' '.join(line)
