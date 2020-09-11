from core import svrsvc, msgext, msgftr, msgsvc, proch, util


def left_chop_and_strip(line, keyword):
    index = line.find(keyword)
    if index == -1:
        return line
    return line[index + len(keyword):].strip()


def right_chop_and_strip(line, keyword):
    index = line.find(keyword)
    if index == -1:
        return line
    return line[:index].strip()


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
        value = right_chop_and_strip(message.get_data(), ' ')
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
            value = left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.VERSION)
            value = right_chop_and_strip(value, 'demo=')
        elif ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            key = 'port'
            value = left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.PORT)
            value = int(value)
        elif ServerDetailsSubscriber.STEAMID_FILTER.accepts(message):
            key = 'steamid'
            value = left_chop_and_strip(message.get_data(), ServerDetailsSubscriber.STEAMID)
        if key:
            svrsvc.ServerStatus.notify_details(self.mailer, self, {key: value})


class CaptureSteamidSubscriber:
    REQUEST = 'CaptureSteadIdSubscriber.Request'
    RESPONSE = 'CaptureSteadIdSubscriber.Response'
    REQUEST_FILTER = msgftr.NameIs(REQUEST)
    KEYSTRING = 'Java_zombie_core_znet_SteamGameServer_BUpdateUserData'
    FILTER = msgftr.Or((
        msgftr.And((
            proch.Filter.STDOUT_LINE,
            msgftr.DataStrContains(KEYSTRING)
        )),
        REQUEST_FILTER
    ))

    def __init__(self, mailer):
        self.mailer = mailer
        self.steamids = {}

    @staticmethod
    async def request(mailer, source):
        messenger = msgext.SynchronousMessenger(mailer)
        response = await messenger.request(msgsvc.Message(source, CaptureSteamidSubscriber.REQUEST))
        return response.get_data()

    def accepts(self, message):
        return CaptureSteamidSubscriber.FILTER.accepts(message)

    def handle(self, message):
        if CaptureSteamidSubscriber.REQUEST_FILTER.accepts(message):
            self.mailer.post((self, CaptureSteamidSubscriber.RESPONSE, self.steamids.copy(), message))
            return None
        line = left_chop_and_strip(message.get_data(), CaptureSteamidSubscriber.KEYSTRING)
        name, steamid = line.split(' id=')
        name = name[1:len(name) - 1]
        names = util.get(steamid, self.steamids)
        if names:
            if name not in names:
                names.append(name)
        else:
            self.steamids.update({steamid: [name]})
        return None
