import typing
from core import svrsvc, msgext, msgftr, proch, util, msgabc
from servers.projectzomboid import domain as dom


class ConsoleLogFilter(msgabc.Filter):
    COMMANDS = (
        'save', 'servermsg', 'chopper', 'gunshot', 'startrain', 'stoprain',
        'players', 'setaccesslevel', 'kickuser', 'additem', 'addvehicle', 'createhorde',
        'addusertowhitelist', 'addxp', 'godmod', 'invisible', 'noclip',
        'addalltowhitelist', 'adduser', 'removeuserfromwhitelist',
        'banuser', 'unbanuser', 'banid', 'unbanid',
        'showoptions', 'changeoption', 'reloadoptions',
        'alarm', 'teleport', 'teleportto', 'voiceban',
        'releasesafehouse', 'reloadlua', 'sendpulse')

    def accepts(self, message):
        if not (proch.Filter.STDOUT_LINE.accepts(message) or proch.Filter.STDERR_LINE.accepts(message)):
            return False
        value = util.right_chop_and_strip(message.data(), ' ')
        return value not in ConsoleLogFilter.COMMANDS


CONSOLE_LOG_FILTER = ConsoleLogFilter()


class ServerDetailsSubscriber(msgabc.Subscriber):
    VERSION = 'versionNumber='
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    PORT = 'server is listening on port'
    PORT_FILTER = msgftr.DataStrContains(PORT)
    STEAMID = 'Server Steam ID'
    STEAMID_FILTER = msgftr.DataStrContains(STEAMID)
    FILTER = msgftr.And(
        proch.Filter.STDOUT_LINE,
        msgftr.Or(VERSION_FILTER, PORT_FILTER, STEAMID_FILTER))

    def __init__(self, mailer: msgabc.MulticastMailer, host: str):
        self._mailer = mailer
        self._host = host

    def accepts(self, message):
        return ServerDetailsSubscriber.FILTER.accepts(message)

    def handle(self, message):
        data = None
        if ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), ServerDetailsSubscriber.VERSION)
            value = util.right_chop_and_strip(value, 'demo=')
            data = {'version': value}
        elif ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), ServerDetailsSubscriber.PORT)
            data = {'host': self._host, 'port': int(value)}
        elif ServerDetailsSubscriber.STEAMID_FILTER.accepts(message):
            value = util.left_chop_and_strip(message.data(), ServerDetailsSubscriber.STEAMID)
            data = {'steamid': int(value)}
        if data:
            svrsvc.ServerStatus.notify_details(self._mailer, self, data)
        return None


class PlayerEventSubscriber(msgabc.Subscriber):
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
        proch.Filter.STDOUT_LINE,
        msgftr.Or(LOGIN_KEY_FILTER, LOGOUT_KEY_FILTER))

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer

    def accepts(self, message):
        return PlayerEventSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if PlayerEventSubscriber.LOGIN_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.data(), PlayerEventSubscriber.LOGIN_KEY)
            name, steamid = line.split(' id=')
            event = dom.PlayerEvent('login', dom.Player(steamid, name[1:-1]))
            self._mailer.post(self, PlayerEventSubscriber.LOGIN, event)
        if PlayerEventSubscriber.LOGOUT_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.data(), PlayerEventSubscriber.LOGOUT_KEY)
            parts = line.split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            event = dom.PlayerEvent('logout', dom.Player(steamid, name[1:-1]))
            self._mailer.post(self, PlayerEventSubscriber.LOGOUT, event)
        return None


class CaptureSteamidSubscriber(msgabc.Subscriber):
    REQUEST = 'CaptureSteadIdSubscriber.Request'
    RESPONSE = 'CaptureSteadIdSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)
    FILTER = msgftr.Or(REQUEST_FILTER, PlayerEventSubscriber.LOGIN_FILTER)

    def __init__(self, mailer: msgabc.Mailer):
        self._mailer = mailer
        self._playerstore = dom.PlayerStore()

    @staticmethod
    async def get_playerstore(mailer: msgabc.MulticastMailer, source: typing.Any) -> dom.PlayerStore:
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(source, CaptureSteamidSubscriber.REQUEST)
        return response.data()

    def accepts(self, message):
        return CaptureSteamidSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if CaptureSteamidSubscriber.REQUEST_FILTER.accepts(message):
            self._mailer.post(self, CaptureSteamidSubscriber.RESPONSE, self._playerstore, message)
        if PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            self._playerstore.add_player(message.data().player())
        return None


class ProvideAdminPasswordSubscriber(msgabc.Subscriber):
    FILTER = msgftr.And(
        proch.Filter.STDOUT_LINE,
        msgftr.Or(
            msgftr.DataStrContains('Enter new administrator password'),
            msgftr.DataStrContains('Confirm the password')))

    def __init__(self, mailer: msgabc.MulticastMailer, pwd: str):
        self._mailer = mailer
        self._pwd = pwd

    def accepts(self, message):
        return ProvideAdminPasswordSubscriber.FILTER.accepts(message)

    async def handle(self, message):
        await proch.PipeInLineService.request(self._mailer, self, self._pwd, force=True)
        return None
