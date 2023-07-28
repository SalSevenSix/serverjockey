import typing
from collections.abc import Iterable
# ALLOW core.* projectzomboid.messaging
from core.util import util
from core.msg import msgabc, msgext, msgftr
from core.proc import proch
from servers.projectzomboid import messaging as msg


class Option:

    def __init__(self, option: str, value: str):
        self._data = {'option': option, 'value': value}

    def option(self) -> str:
        return self._data['option']

    def asdict(self) -> dict:
        return self._data.copy()


class Player:

    def __init__(self, steamid: str, name: str):
        self._data = {'steamid': steamid, 'name': name}

    def steamid(self) -> str:
        return self._data['steamid']

    def name(self) -> str:
        return self._data['name']

    def asdict(self) -> dict:
        return self._data.copy()


class PlayerEvent:

    def __init__(self, event: str, player: Player):
        self._event = event
        self._player = player

    def player(self) -> Player:
        return self._player

    def asdict(self) -> dict:
        return {'event': self._event, 'player': self._player.asdict()}


class OptionLoader:

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any):
        self._mailer = mailer
        self._source = source

    async def all(self) -> typing.Collection[Option]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'showoptions', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('List of Server Options:'), include_start=False,
                stop_filter=msgftr.DataStrContains('ServerWelcomeMessage'), include_stop=True,
                timeout=10.0))
        options = []
        if response is None or not isinstance(response, Iterable):
            return options
        for line in [m.data() for m in response]:
            if line.startswith('* '):
                option, value = line[2:].split('=')
                options.append(Option(option, value))
        return options

    async def get(self, option: str) -> typing.Optional[Option]:
        if option is None:
            return None
        options = [o for o in await self.all() if o.option() == option]
        return util.single(options)


class PlayerLoader:

    def __init__(self, mailer: msgabc.MulticastMailer, source: typing.Any):
        self._mailer = mailer
        self._source = source

    async def all(self) -> typing.Collection[Player]:
        response = await proch.PipeInLineService.request(
            self._mailer, self._source, 'players', msgext.MultiCatcher(
                catch_filter=proch.ServerProcess.FILTER_STDOUT_LINE,
                start_filter=msgftr.DataStrContains('Players connected'), include_start=False,
                stop_filter=msgftr.DataEquals(''), include_stop=False,
                timeout=10.0))
        players = []
        if response is None or not isinstance(response, Iterable):
            return players
        playerstore = await PlayerStoreService.get(self._mailer, self._source)
        for line in [m.data() for m in response]:
            if line.startswith('-'):
                name = line[1:]
                steamid = playerstore.find_steamid(name)
                players.append(Player(steamid, name))
        return players

    async def get(self, name: str) -> typing.Optional[Player]:
        if name is None:
            return None
        players = [o for o in await self.all() if o.name() == name]
        return util.single(players)


class PlayerStore:

    def __init__(self):
        self._data: typing.Dict[str, typing.List[str]] = {}

    def add_player(self, player: Player):
        names = util.get(player.steamid(), self._data)
        if names:
            if player.name() not in names:
                names.append(player.name())
        else:
            self._data.update({player.steamid(): [player.name()]})

    def find_steamid(self, name: str) -> typing.Optional[str]:
        for steamid, names in self._data.items():
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


class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    CLEAR = 'PlayerActivitySubscriber.Clear'
    CLEAR_FILTER = msgftr.NameIs(CLEAR)
    LOGIN = 'PlayerActivitySubscriber.Login'
    LOGIN_FILTER = msgftr.NameIs(LOGIN)
    LOGIN_KEY = '> ConnectionManager: [fully-connected]'
    LOGIN_KEY_FILTER = msgftr.DataStrContains(LOGIN_KEY)
    LOGOUT = 'PlayerActivitySubscriber.Logout'
    LOGOUT_FILTER = msgftr.NameIs(LOGOUT)
    LOGOUT_KEY = '> Disconnected player'
    LOGOUT_KEY_FILTER = msgftr.DataStrContains(LOGOUT_KEY)

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.Or(
            proch.ServerProcess.FILTER_STATES_DOWN,
            msgftr.And(
                msg.CONSOLE_OUTPUT_FILTER,
                msgftr.Or(_PlayerEventSubscriber.LOGIN_KEY_FILTER,
                          _PlayerEventSubscriber.LOGOUT_KEY_FILTER))))
        self._mailer = mailer

    def handle(self, message):
        if proch.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            self._mailer.post(self, _PlayerEventSubscriber.CLEAR, {'event': 'clear'})
            return None
        if _PlayerEventSubscriber.LOGIN_KEY_FILTER.accepts(message):
            steamid = str(message.data())
            steamid = util.left_chop_and_strip(steamid, 'steam-id=')
            steamid = util.right_chop_and_strip(steamid, 'access=')
            name = str(message.data())
            name = util.left_chop_and_strip(name, 'username="')
            name = util.right_chop_and_strip(name, '" connection-type=')
            event = PlayerEvent('login', Player(steamid, name))
            self._mailer.post(self, _PlayerEventSubscriber.LOGIN, event)
            return None
        if _PlayerEventSubscriber.LOGOUT_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.data(), _PlayerEventSubscriber.LOGOUT_KEY)
            parts = line.split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            event = PlayerEvent('logout', Player(steamid, name[1:-1]))
            self._mailer.post(self, _PlayerEventSubscriber.LOGOUT, event)
            return None
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


PLAYER_EVENT_FILTER = msgftr.Or(
    _PlayerEventSubscriber.CLEAR_FILTER,
    _PlayerEventSubscriber.LOGIN_FILTER,
    _PlayerEventSubscriber.LOGOUT_FILTER)
