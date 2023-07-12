import typing
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.msg import msgabc, msgftr, msgext
from core.http import httpabc
from core.proc import proch
from core.util import util


class PlayersSubscriber(msgabc.AbcSubscriber):
    EVENT = 'PlayersSubscriber.Event'
    EVENT_FILTER = msgftr.NameIs(EVENT)
    GET = 'PlayersSubscriber.Get'
    GET_FILTER = msgftr.NameIs(GET)
    GET_RESPONSE = 'PlayersSubscriber.GetResponse'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            PlayersSubscriber.EVENT_FILTER,
            PlayersSubscriber.GET_FILTER,
            proch.ServerProcess.FILTER_STATES_DOWN))
        self._mailer = mailer
        self._players = []

    @staticmethod
    def event_login(mailer: msgabc.Mailer, source: typing.Any, name: str):
        mailer.post(source, PlayersSubscriber.EVENT, {'event': 'login', 'player': {'name': name}})

    @staticmethod
    def event_logout(mailer: msgabc.Mailer, source: typing.Any, name: str):
        mailer.post(source, PlayersSubscriber.EVENT, {'event': 'logout', 'player': {'name': name}})

    @staticmethod
    def event_chat(mailer: msgabc.Mailer, source: typing.Any, name: str, text: str):
        mailer.post(source, PlayersSubscriber.EVENT, {'event': 'chat', 'player': {'name': name}, 'text': text})

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, PlayersSubscriber.GET)
        return response.data()

    def handle(self, message):
        if proch.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._mailer.post(self, PlayersSubscriber.EVENT, {'event': 'clear'})
            return None
        if PlayersSubscriber.EVENT_FILTER.accepts(message):
            event_type = util.get('event', message.data())
            if event_type == 'chat':
                return None
            if event_type == 'clear':
                self._players = []
                return None
            players, player = [], util.get('player', message.data())
            for current in self._players:
                if player['name'] != current['name']:
                    players.append(current)
            if event_type == 'login':
                players.append(player)
            self._players = players
            return None
        if PlayersSubscriber.GET_FILTER.accepts(message):
            self._mailer.post(self, PlayersSubscriber.GET_RESPONSE, tuple(self._players), message)
            return None
        return None


class PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await PlayersSubscriber.get(self._mailer, self)
