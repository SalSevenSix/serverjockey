import typing
from core.util import util
from core.msg import msgabc, msgext, msgftr
from core.proc import proch
from servers.projectzomboid import domain as dom


class PlayerStore:

    def __init__(self):
        self._data: typing.Dict[str, typing.List[str]] = {}

    def add_player(self, player: dom.Player):
        names = util.get(player.steamid(), self._data)
        if names:
            if player.name() not in names:
                names.append(player.name())
        else:
            self._data.update({player.steamid(): [player.name()]})

    def find_steamid(self, name: str) -> typing.Optional[str]:
        for steamid, names in iter(self._data.items()):
            if name in names:
                return steamid
        return None

    def asdict(self) -> dict:
        return self._data.copy()


class PlayerStoreService:

    def __init__(self, mailer: msgabc.MulticastMailer):
        self._mailer = mailer

    def initialise(self):
        self._mailer.register(_CaptureSteamidSubscriber(self._mailer))
        self._mailer.register(_PlayerEventSubscriber(self._mailer))

    @staticmethod
    async def get(mailer: msgabc.MulticastMailer, source: typing.Any) -> PlayerStore:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, _CaptureSteamidSubscriber.REQUEST)
        return response.data()


class PlayerEvent:

    def __init__(self, event: str, player: dom.Player):
        self._created = util.now_millis()
        self._event = event
        self._player = player

    def player(self) -> dom.Player:
        return self._player

    def asdict(self) -> dict:
        return {'created': self._created, 'event': self._event, 'player': self._player.asdict()}


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    LOGIN = 'PlayerActivitySubscriber.Login'
    LOGIN_FILTER = msgftr.NameIs(LOGIN)
    LOGIN_KEY = 'Java_zombie_core_znet_SteamGameServer_BUpdateUserData'
    LOGIN_KEY_FILTER = msgftr.DataStrContains(LOGIN_KEY)
    LOGOUT = 'PlayerActivitySubscriber.Logout'
    LOGOUT_FILTER = msgftr.NameIs(LOGOUT)
    LOGOUT_KEY = 'Disconnected player'
    LOGOUT_KEY_FILTER = msgftr.DataStrContains(LOGOUT_KEY)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            proch.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.LOGIN_KEY_FILTER, _PlayerEventSubscriber.LOGOUT_KEY_FILTER)))
        self._mailer = mailer

    def handle(self, message):
        if _PlayerEventSubscriber.LOGIN_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LOGIN_KEY)
            name, steamid = line.split(' id=')
            event = PlayerEvent('login', dom.Player(steamid, name[1:-1]))
            self._mailer.post(self, _PlayerEventSubscriber.LOGIN, event)
        if _PlayerEventSubscriber.LOGOUT_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LOGOUT_KEY)
            parts = line.split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            event = PlayerEvent('logout', dom.Player(steamid, name[1:-1]))
            self._mailer.post(self, _PlayerEventSubscriber.LOGOUT, event)
        return None


class _CaptureSteamidSubscriber(msgabc.AbcSubscriber):
    REQUEST = 'CaptureSteadIdSubscriber.Request'
    RESPONSE = 'CaptureSteadIdSubscriber.Response'

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(msgftr.NameIs(_CaptureSteamidSubscriber.REQUEST),
                                   _PlayerEventSubscriber.LOGIN_FILTER))
        self._mailer = mailer
        self._playerstore = PlayerStore()

    def handle(self, message):
        if message.name() is _CaptureSteamidSubscriber.REQUEST:
            self._mailer.post(self, _CaptureSteamidSubscriber.RESPONSE, self._playerstore, message)
        else:
            self._playerstore.add_player(message.data().player())
        return None


PLAYER_EVENT_FILTER = msgftr.Or(_PlayerEventSubscriber.LOGIN_FILTER, _PlayerEventSubscriber.LOGOUT_FILTER)
