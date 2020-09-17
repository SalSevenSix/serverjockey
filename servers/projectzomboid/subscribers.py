from core import svrsvc, msgext, msgftr, msgsvc, proch, util, httpsvc
from servers.projectzomboid import domain as d


class ConsoleLogFilter:
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
        value = util.right_chop_and_strip(message.get_data(), ' ')
        return value not in ConsoleLogFilter.COMMANDS


class ServerStateSubscriber:
    STATE_MAP = {
        proch.ProcessHandler.STATE_START: 'START',
        proch.ProcessHandler.STATE_STARTING: 'STARTING',
        proch.ProcessHandler.STATE_STARTED: 'STARTED',
        proch.ProcessHandler.STATE_TIMEOUT: 'TIMEOUT',
        proch.ProcessHandler.STATE_TERMINATED: 'TERMINATED',
        proch.ProcessHandler.STATE_EXCEPTION: 'EXCEPTION',
        proch.ProcessHandler.STATE_COMPLETE: 'COMPLETE',
    }

    def __init__(self, mailer):
        self.mailer = mailer

    def accepts(self, message):
        return proch.Filter.PROCESS_STATE_ALL.accepts(message)

    def handle(self, message):
        state = util.get(message.get_name(), ServerStateSubscriber.STATE_MAP)
        state = state if state else 'UNKNOWN'
        svrsvc.ServerStatus.notify_state(self.mailer, self, state)


class ServerDetailsSubscriber:
    VERSION = 'versionNumber='
    VERSION_FILTER = msgftr.DataStrContains(VERSION)
    PORT = 'server is listening on port'
    PORT_FILTER = msgftr.DataStrContains(PORT)
    STEAMID = 'Server Steam ID'
    STEAMID_FILTER = msgftr.DataStrContains(STEAMID)
    FILTER = msgftr.And((
        proch.Filter.STDOUT_LINE,
        msgftr.Or((VERSION_FILTER, PORT_FILTER, STEAMID_FILTER))
    ))

    def __init__(self, mailer):
        self.mailer = mailer

    def accepts(self, message):
        return ServerDetailsSubscriber.FILTER.accepts(message)

    def handle(self, message):
        key, value = None, None
        if ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            key = 'version'
            value = util.left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.VERSION)
            value = util.right_chop_and_strip(value, 'demo=')
        elif ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            key = 'port'
            value = util.left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.PORT)
            value = int(value)
        elif ServerDetailsSubscriber.STEAMID_FILTER.accepts(message):
            key = 'steamid'
            value = util.left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.STEAMID)
        if key:
            svrsvc.ServerStatus.notify_details(self.mailer, self, {key: value})


class PlayerEventSubscriber:
    LOGIN = 'PlayerActivitySubscriber.Login'
    LOGIN_FILTER = msgftr.NameIs(LOGIN)
    LOGIN_KEY = 'Java_zombie_core_znet_SteamGameServer_BUpdateUserData'
    LOGIN_KEY_FILTER = msgftr.DataStrContains(LOGIN_KEY)
    LOGOUT = 'PlayerActivitySubscriber.Logout'
    LOGOUT_FILTER = msgftr.NameIs(LOGOUT)
    LOGOUT_KEY = 'Disconnected player'
    LOGOUT_KEY_FILTER = msgftr.DataStrContains(LOGOUT_KEY)
    ALL_FILTER = msgftr.Or((LOGIN_FILTER, LOGOUT_FILTER))
    FILTER = msgftr.And((
        proch.Filter.STDOUT_LINE,
        msgftr.Or((LOGIN_KEY_FILTER, LOGOUT_KEY_FILTER))
    ))

    def __init__(self, mailer):
        self.mailer = mailer

    def accepts(self, message):
        return PlayerEventSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if PlayerEventSubscriber.LOGIN_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.get_data(), PlayerEventSubscriber.LOGIN_KEY)
            name, steamid = line.split(' id=')
            event = d.PlayerEvent('login', d.Player(steamid, name[1:-1]))
            self.mailer.post((self, PlayerEventSubscriber.LOGIN, event))
        if PlayerEventSubscriber.LOGOUT_KEY_FILTER.accepts(message):
            line = util.left_chop_and_strip(message.get_data(), PlayerEventSubscriber.LOGOUT_KEY)
            parts = line.split(' ')
            steamid, name = parts[-1], ' '.join(parts[:-1])
            event = d.PlayerEvent('logout', d.Player(steamid, name[1:-1]))
            self.mailer.post((self, PlayerEventSubscriber.LOGOUT, event))
        return None


class CaptureSteamidSubscriber:
    REQUEST = 'CaptureSteadIdSubscriber.Request'
    RESPONSE = 'CaptureSteadIdSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)
    FILTER = msgftr.Or((REQUEST_FILTER, PlayerEventSubscriber.LOGIN_FILTER))

    def __init__(self, mailer):
        self.mailer = mailer
        self.playerstore = d.PlayerStore()

    @staticmethod
    async def get_playerstore(mailer, source):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, CaptureSteamidSubscriber.REQUEST))
        return response.get_data()

    def accepts(self, message):
        return CaptureSteamidSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if CaptureSteamidSubscriber.REQUEST_FILTER.accepts(message):
            self.mailer.post((self, CaptureSteamidSubscriber.RESPONSE, self.playerstore, message))
        if PlayerEventSubscriber.LOGIN_FILTER.accepts(message):
            self.playerstore.add_player(message.get_data().get_player())
        return None


class ProvideAdminPasswordSubscriber:
    SECRET_FILTER = msgftr.NameIs(httpsvc.Secret.NAME)
    SOLICIT_FILTER = msgftr.And((
        proch.Filter.STDOUT_LINE,
        msgftr.Or((
            msgftr.DataStrContains('Enter new administrator password'),
            msgftr.DataStrContains('Confirm the password')
        ))
    ))
    FILTER = msgftr.Or((SECRET_FILTER, SOLICIT_FILTER))

    def __init__(self, mailer):
        self.mailer = mailer
        self.pwd = 'admin'

    def accepts(self, message):
        return ProvideAdminPasswordSubscriber.FILTER.accepts(message)

    async def handle(self, message):
        if ProvideAdminPasswordSubscriber.SECRET_FILTER.accepts(message):
            self.pwd = message.get_data()
        if ProvideAdminPasswordSubscriber.SOLICIT_FILTER.accepts(message):
            await proch.PipeInLineService.request(self.mailer, self, self.pwd, force=True)
        return None
