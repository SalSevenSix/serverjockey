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


class _PlayerEventSubscriber(msgabc.Subscriber):
    LOGIN = 'PlayerActivitySubscriber.Login'
    LOGIN_FILTER = msgftr.NameIs(LOGIN)
    LOGIN_KEY = 'Java_zombie_core_znet_SteamGameServer_BUpdateUserData'
    LOGIN_KEY_FILTER = msgftr.DataStrContains(LOGIN_KEY)
    LOGOUT = 'PlayerActivitySubscriber.Logout'
    LOGOUT_FILTER = msgftr.NameIs(LOGOUT)
    LOGOUT_KEY = 'Disconnected player'
    LOGOUT_KEY_FILTER = msgftr.DataStrContains(LOGOUT_KEY)
    ALL_FILTER = msgftr.Or(LOGIN_FILTER, LOGOUT_FILTER)
    FILTER = msgftr.And(
        proch.ServerProcess.FILTER_STDOUT_LINE,
        msgftr.Or(LOGIN_KEY_FILTER, LOGOUT_KEY_FILTER))

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer

    def accepts(self, message):
        return _PlayerEventSubscriber.FILTER.accepts(message)

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


class _CaptureSteamidSubscriber(msgabc.Subscriber):
    REQUEST = 'CaptureSteadIdSubscriber.Request'
    RESPONSE = 'CaptureSteadIdSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)
    FILTER = msgftr.Or(REQUEST_FILTER, _PlayerEventSubscriber.LOGIN_FILTER)

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer
        self._playerstore = PlayerStore()

    def accepts(self, message):
        return _CaptureSteamidSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if _CaptureSteamidSubscriber.REQUEST_FILTER.accepts(message):
            self._mailer.post(self, _CaptureSteamidSubscriber.RESPONSE, self._playerstore, message)
        if _PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            self._playerstore.add_player(message.data().player())
        return None
