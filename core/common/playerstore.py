from __future__ import annotations
import typing
# ALLOW util.* msg*.* context.* http.* system.* proc.*
from core.util import dtutil
from core.msg import msgabc, msgftr, msgext
from core.msgc import mc
from core.http import httpabc, httpsec
from core.system import svrsvc


class PlayersHandler(httpabc.GetHandler):

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        return await PlayersSubscriber.get(self._mailer, self)


class PlayersSubscriber(msgabc.AbcSubscriber):
    GET = 'PlayersSubscriber.Get'
    GET_FILTER = msgftr.NameIs(GET)
    GET_RESPONSE = 'PlayersSubscriber.GetResponse'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            mc.PlayerStore.EVENT_FILTER,
            PlayersSubscriber.GET_FILTER,
            svrsvc.ServerStatus.RUNNING_FALSE_FILTER))
        self._mailer = mailer
        self._players = _Players()

    @staticmethod
    def event_login(mailer: msgabc.Mailer, source: typing.Any, name: str, steamid: str | None = None):
        mailer.post(source, mc.PlayerStore.EVENT, _EventLogin(name, steamid))

    @staticmethod
    def event_logout(mailer: msgabc.Mailer, source: typing.Any, name: str, steamid: str | None = None):
        mailer.post(source, mc.PlayerStore.EVENT, _EventLogout(name, steamid))

    @staticmethod
    def event_chat(mailer: msgabc.Mailer, source: typing.Any, name: str, text: str):
        mailer.post(source, mc.PlayerStore.EVENT, _EventChat(name, text))

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any,
                  canonical: typing.Optional[typing.Collection[Player]] = None):
        response = await msgext.SynchronousMessenger(mailer).request(source, PlayersSubscriber.GET, canonical)
        return response.data()

    def handle(self, message):
        if mc.PlayerStore.EVENT_FILTER.accepts(message):
            event = message.data()
            if isinstance(event, (_EventLogin, _EventLogout)):
                self._players.login_or_logout(event)
            elif isinstance(event, _EventClear):
                self._players.clear()
            return None
        if svrsvc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            self._mailer.post(self, mc.PlayerStore.EVENT, _EventClear())
            return None
        if PlayersSubscriber.GET_FILTER.accepts(message):
            data = self._players.get(message.data())
            self._mailer.post(self, PlayersSubscriber.GET_RESPONSE, data, message)
            return None
        return None


class Player:

    def __init__(self, name: str, steamid: str | None = None, startmillis: int = -1):
        self._name, self._steamid, self._startmillis = name, steamid, startmillis

    def name(self) -> str:
        return self._name

    def is_same(self, player: Player) -> bool:
        return self._name == player._name

    def update(self, player: Player):
        if self._steamid is None or (self._steamid == '' and player._steamid):
            self._steamid = player._steamid
        if self._startmillis == -1:
            self._startmillis = player._startmillis

    def asdict(self) -> dict:
        result = {'name': self._name, 'steamid': self._steamid}
        if self._startmillis > -1:
            result['startmillis'] = self._startmillis
            result['uptime'] = dtutil.now_millis() - self._startmillis
        return result


class _Players:

    def __init__(self):
        self._players = []

    def clear(self):
        self._players = []

    def login_or_logout(self, event):
        players, player = [], event.player()
        for current in self._players:
            if not player.is_same(current):
                players.append(current)
        if isinstance(event, _EventLogin):
            players.append(player)
        self._players = players

    def get(self, canonical: typing.Optional[typing.Collection[Player]]) -> tuple:
        if canonical is None:
            return tuple([o.asdict() for o in self._players])
        if len(canonical) == 0:
            return ()
        keyed, players = self._keyed(), []
        for current in canonical:
            if current.name() in keyed:
                stored = keyed[current.name()]
                stored.update(current)
                players.append(stored.asdict())
            else:
                players.append(current.asdict())
        return tuple(players)

    def _keyed(self) -> dict:
        result = {}
        for current in self._players:
            result[current.name()] = current
        return result


# TODO use uppercase event names from core.msgc.sc

class _EventLogin:

    def __init__(self, name: str, steamid: str | None = None):
        self._player = Player(name, steamid, dtutil.now_millis())

    def player(self) -> Player:
        return self._player

    def asdict(self) -> dict:
        return {'event': 'login', 'player': self._player.asdict()}


class _EventChat:

    def __init__(self, name: str, text: str):
        self._player = Player(name)
        self._text = text

    def asdict(self) -> dict:
        return {'event': 'chat', 'player': self._player.asdict(), 'text': self._text}


class _EventLogout:

    def __init__(self, name: str, steamid: str | None = None):
        self._player = Player(name, steamid)

    def player(self) -> Player:
        return self._player

    def asdict(self) -> dict:
        return {'event': 'logout', 'player': self._player.asdict()}


class _EventClear:

    # noinspection PyMethodMayBeStatic
    def asdict(self) -> dict:
        return {'event': 'clear'}
