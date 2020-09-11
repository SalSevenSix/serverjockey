from core import util


class Noop:

    def transform(self, message):
        return message


class GetData:

    def transform(self, message):
        return message.get_data()


class ToString:

    def transform(self, message):
        text = ' '.join((util.timestamp(message.get_created()),
                         str(message.get_id()),
                         str(message.get_name()).ljust(32),
                         util.obj_to_str(message.get_data())))
        if message.get_reply_to() is not None:
            text = text + ' [' + self.transform(message.get_reply_to()) + ']'
        return text


class ToJson:

    def transform(self, message):
        return util.obj_to_json(message)
