# ALLOW core.*
from core.util import util, sysutil
from core.msg import msgabc, msgftr, msglog, msgext
from core.msgc import mc
from core.system import svrsvc, svrext
from core.proc import jobh, prcext
from core.common import playerstore

SERVER_STARTED_FILTER = msgftr.And(mc.ServerProcess.FILTER_STDOUT_LINE, msgftr.DataStrContains('INF StartGame done'))
CONSOLE_LOG_FILTER = msgftr.Or(
    mc.ServerProcess.FILTER_ALL_LINES,
    jobh.JobProcess.FILTER_ALL_LINES,
    msglog.FILTER_ALL_LEVELS)
CONSOLE_LOG_ERROR_FILTER = msgftr.And(
    mc.ServerProcess.FILTER_ALL_LINES,
    msgftr.DataMatches(r'^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d \d*\.\d* ERR .*'))
MAINTENANCE_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_STARTED, msgext.Archiver.FILTER_START, msgext.Unpacker.FILTER_START)
READY_STATE_FILTER = msgftr.Or(
    jobh.JobProcess.FILTER_DONE, msgext.Archiver.FILTER_DONE, msgext.Unpacker.FILTER_DONE)


async def initialise(mailer: msgabc.MulticastMailer):
    mailer.register(prcext.ServerStateSubscriber(mailer))
    mailer.register(svrext.MaintenanceStateSubscriber(mailer, MAINTENANCE_STATE_FILTER, READY_STATE_FILTER))
    mailer.register(playerstore.PlayersSubscriber(mailer))
    mailer.register(_ServerDetailsSubscriber(mailer, await sysutil.public_ip()))
    mailer.register(_PlayerEventSubscriber(mailer))


class _ServerDetailsSubscriber(msgabc.AbcSubscriber):
    VERSION_PREFIX, VERSION_SUFFIX = 'INF Version:', 'Compatibility Version:'
    VERSION_FILTER = msgftr.DataMatches('.*' + VERSION_PREFIX + '.*' + VERSION_SUFFIX + '.*')
    PORT_PREFIX = 'GamePref.ConnectToServerPort ='
    PORT_FILTER = msgftr.DataStrContains(PORT_PREFIX)
    CON_PORT_PREFIX = 'GamePref.UNUSED_ControlPanelPort ='
    CON_PORT_FILTER = msgftr.DataStrContains(CON_PORT_PREFIX)

    def __init__(self, mailer: msgabc.Mailer, public_ip: str):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(
                _ServerDetailsSubscriber.VERSION_FILTER,
                _ServerDetailsSubscriber.PORT_FILTER,
                _ServerDetailsSubscriber.CON_PORT_FILTER)))
        self._mailer, self._public_ip = mailer, public_ip

    def handle(self, message):
        if _ServerDetailsSubscriber.VERSION_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.VERSION_PREFIX)
            value = util.rchop(value, _ServerDetailsSubscriber.VERSION_SUFFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(version=value))
            return None
        if _ServerDetailsSubscriber.PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.PORT_PREFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(ip=self._public_ip, port=value))
            return None
        if _ServerDetailsSubscriber.CON_PORT_FILTER.accepts(message):
            value = util.lchop(message.data(), _ServerDetailsSubscriber.CON_PORT_PREFIX)
            svrsvc.ServerStatus.notify_details(self._mailer, self, dict(cport=value))
            return None
        return None


# 2024-08-14T19:39:28 236.252 INF GMSG: Player 'Apollo' joined the game
# 2024-08-14T19:39:28 236.260 INF PlayerSpawnedInWorld (reason: EnterMultiplayer, position: -1280, 61, 209): EntityID=171, PltfmId='Steam_76561197968989085', CrossId='EOS_00023f168ede4136a17c954ec0b9245d', OwnerID='Steam_76561197968989085', PlayerName='Apollo', ClientNumber='1'
# 2024-08-15T14:19:33 291.194 INF PlayerSpawnedInWorld (reason: JoinMultiplayer, position: -1274, 61, 213): EntityID=171, PltfmId='Steam_76561197968989085', CrossId='EOS_00023f168ede4136a17c954ec0b9245d', OwnerID='Steam_76561197968989085', PlayerName='Apollo', ClientNumber='1'
# 2024-08-14T19:39:41 249.091 INF Chat (from 'Steam_76561197968989085', entity id '171', to 'Global'): hello all old
# 2024-12-18T11:50:33 369.738 INF Chat (from 'Steam_76561197968989085', entity id '171', to 'Global'): 'Apollo': hello from game new
# 2024-08-14T19:39:45 253.185 INF Player Apollo disconnected after 0.4 minutes
# 2024-08-14T19:39:45 253.479 INF Player disconnected: EntityID=171, PltfmId='Steam_76561197968989085', CrossId='EOS_00023f168ede4136a17c954ec0b9245d', OwnerID='Steam_76561197968989085', PlayerName='Apollo', ClientNumber='1'
# 2024-08-14T19:39:45 253.490 INF GMSG: Player 'Apollo' left the game
# 2024-11-29T23:49:36 252.509 INF GMSG: Player 'Apollo' died
class _PlayerEventSubscriber(msgabc.AbcSubscriber):
    JOIN_FILTER = msgftr.DataMatches(r'.*INF GMSG: Player \'.*\' joined the game$')
    SPAWN_FILTER = msgftr.DataMatches(r'.*INF PlayerSpawnedInWorld \(reason.*OwnerID=\'.*PlayerName=\'.*\', ClientNumber=.*')
    CHAT_FILTER = msgftr.DataMatches(r'.*INF Chat \(from \'.*\', to \'Global\'\):.*')
    LEAVE_FILTER = msgftr.DataMatches(r'.*INF GMSG: Player \'.*\' left the game$')
    DEATH_FILTER = msgftr.DataMatches(r'.*INF GMSG: Player \'.*\' died$')

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(msgftr.And(
            mc.ServerProcess.FILTER_STDOUT_LINE,
            msgftr.Or(_PlayerEventSubscriber.CHAT_FILTER,
                      _PlayerEventSubscriber.JOIN_FILTER,
                      _PlayerEventSubscriber.SPAWN_FILTER,
                      _PlayerEventSubscriber.LEAVE_FILTER,
                      _PlayerEventSubscriber.DEATH_FILTER)))
        self._mailer, self._idmap = mailer, {}

    def handle(self, message):
        value = message.data()
        if _PlayerEventSubscriber.CHAT_FILTER.accepts(message):
            # playerid = util.lchop(value, 'INF Chat (from \'')
            # playerid = util.rchop(playerid, '\', entity id')
            # name = util.get(playerid, self._idmap)
            # if name is None:
            #     return None
            # text = util.lchop(value, 'to \'Global\'):')
            value = util.lchop(value, 'to \'Global\'):')
            name = util.rchop(value, ':')[1:-1]
            text = util.lchop(value, ':')
            playerstore.PlayersSubscriber.event_chat(self._mailer, self, name, text)
            return None
        if _PlayerEventSubscriber.JOIN_FILTER.accepts(message):
            name = util.lchop(value, 'INF GMSG: Player \'')
            name = util.rchop(name, '\' joined the game')
            playerstore.PlayersSubscriber.event_login(self._mailer, self, name)
            return None
        if _PlayerEventSubscriber.SPAWN_FILTER.accepts(message):
            playerid = util.lchop(value, ', OwnerID=\'')
            playerid = util.rchop(playerid, '\', PlayerName=')
            name = util.lchop(value, ', PlayerName=\'')
            name = util.rchop(name, '\', ClientNumber=')
            self._idmap[playerid] = name
            return None
        if _PlayerEventSubscriber.LEAVE_FILTER.accepts(message):
            name = util.lchop(value, 'INF GMSG: Player \'')
            name = util.rchop(name, '\' left the game')
            playerstore.PlayersSubscriber.event_logout(self._mailer, self, name)
            self._idmap = util.delete_dict_by_value(self._idmap, name)
            return None
        if _PlayerEventSubscriber.DEATH_FILTER.accepts(message):
            name = util.lchop(value, 'INF GMSG: Player \'')
            name = util.rchop(name, '\' died')
            playerstore.PlayersSubscriber.event_death(self._mailer, self, name)
            return None
        return None
