from __future__ import annotations
import typing
# ALLOW util.* msg.* context.* http.* system.* proc.*
from core.util import util
from core.msg import msgabc, msgftr, msgext, msgtrf
from core.http import httpabc
from core.system import svrsvc

# TODO add a feature to inject an interface to fetch real list of players


_EVENT = 'PlayersSubscriber.Event'
EVENT_FILTER = msgftr.NameIs(_EVENT)
EVENT_TRF = msgtrf.DataAsDict()


class PlayersSubscriber(msgabc.AbcSubscriber):
    GET = 'PlayersSubscriber.Get'
    GET_FILTER = msgftr.NameIs(GET)
    GET_RESPONSE = 'PlayersSubscriber.GetResponse'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            EVENT_FILTER,
            PlayersSubscriber.GET_FILTER,
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER))
        self._mailer = mailer
        self._players = _Players()

    @staticmethod
    def event_login(mailer: msgabc.Mailer, source: typing.Any, name: str):
        mailer.post(source, _EVENT, _EventLogin(name))

    @staticmethod
    def event_logout(mailer: msgabc.Mailer, source: typing.Any, name: str):
        mailer.post(source, _EVENT, _EventLogout(name))

    @staticmethod
    def event_chat(mailer: msgabc.Mailer, source: typing.Any, name: str, text: str):
        mailer.post(source, _EVENT, _EventChat(name, text))

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, PlayersSubscriber.GET)
        return response.data()

    def handle(self, message):
        if EVENT_FILTER.accepts(message):
            event = message.data()
            if isinstance(event, _EventChat):
                return None
            if isinstance(event, _EventClear):
                self._players.clear()
                return None
            self._players.login_or_logout(event)
            return None
        if svrsvc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            self._mailer.post(self, _EVENT, _EventClear())
            return None
        if PlayersSubscriber.GET_FILTER.accepts(message):
            self._mailer.post(self, PlayersSubscriber.GET_RESPONSE, self._players.asdict(), message)
            return None
        return None


class PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        return await PlayersSubscriber.get(self._mailer, self)


class _Players:

    def __init__(self):
        self._players = []

    def login_or_logout(self, event):
        players, player = [], event.player()
        for current in self._players:
            if not player.is_same(current):
                players.append(current)
        if isinstance(event, _EventLogin):
            players.append(player)
        self._players = players

    def clear(self):
        self._players = []

    def asdict(self) -> tuple:
        players = []
        for current in self._players:
            players.append(current.asdict())
        return tuple(players)


class _Player:

    def __init__(self, name: str, startmillis: int = -1):
        self._name = name
        self._startmillis = startmillis

    def is_same(self, player: _Player) -> bool:
        return self._name == player._name

    def asdict(self) -> dict:
        result = {'name': self._name}
        if self._startmillis > -1:
            result['startmillis'] = self._startmillis
            result['uptime'] = util.now_millis() - self._startmillis
        return result


class _EventLogin:

    def __init__(self, name: str):
        self._player = _Player(name, util.now_millis())

    def player(self) -> _Player:
        return self._player

    def asdict(self) -> dict:
        return {'event': 'login', 'player': self._player.asdict()}


class _EventChat:

    def __init__(self, name: str, text: str):
        self._player = _Player(name)
        self._text = text

    def asdict(self) -> dict:
        return {'event': 'chat', 'player': self._player.asdict(), 'text': self._text}


class _EventLogout:

    def __init__(self, name: str):
        self._player = _Player(name)

    def player(self) -> _Player:
        return self._player

    def asdict(self) -> dict:
        return {'event': 'logout', 'player': self._player.asdict()}


class _EventClear:

    def asdict(self) -> dict:
        return {'event': 'clear'}
