import typing
from core.msg import msgabc, msgftr, msgext
from core.http import httpabc
from servers.factorio import messaging as msg


class PlayersSubscriber(msgabc.AbcSubscriber):
    GET = 'PlayersSubscriber.Get'
    GET_FILTER = msgftr.NameIs(GET)
    GET_RESPONSE = 'PlayersSubscriber.GetResponse'

    def __init__(self, mailer: msgabc.MulticastMailer):
        super().__init__(msgftr.Or(
            PlayersSubscriber.GET_FILTER,
            msg.SERVER_STARTED_FILTER,
            msg.PLAYER_EVENT_FILTER))
        self._mailer = mailer
        self._players = []

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, PlayersSubscriber.GET)
        return response.data()

    def handle(self, message):
        if msg.SERVER_STARTED_FILTER.accepts(message):
            self._players = []
            return None
        if msg.PLAYER_EVENT_FILTER.accepts(message):
            event = message.data()
            if event['event'] == 'join':
                self._players.append(event['name'])
            if event['event'] == 'leave':
                self._players.remove(event['name'])
            return None
        if PlayersSubscriber.GET_FILTER.accepts(message):
            result = [{'steamid': False, 'name': p} for p in self._players]
            self._mailer.post(self, PlayersSubscriber.GET_RESPONSE, result, message)
            return None
        return None


class PlayersHandler(httpabc.AsyncGetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await PlayersSubscriber.get(self._mailer, self)
