# ALLOW util.* msgc.* msg.msgftr msg.msgtrf
from core.msg import msgftr, msgtrf
from core.msgc import sc


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'
    SERVER_FILTER = msgftr.NameIn((SERVER_INITIALISED, SERVER_DELETED))


class ServerService:
    START, RESTART, STOP = 'ServerService.Start', 'ServerService.Restart', 'ServerService.Stop'
    DELETE, DELETE_ME = 'ServerService.Delete', 'ServerService.DeletedMe'
    SHUTDOWN, SHUTDOWN_RESPONSE = 'ServerService.Shutdown', 'ServerService.ShutdownResponse'
    CLEANUP_NAMES = (DELETE, SHUTDOWN)
    CLEANUP_FILTER = msgftr.NameIn(CLEANUP_NAMES)


class ServerStatus:
    REQUEST, RESPONSE = 'ServerStatus.Request', 'ServerStatus.Response'
    NOTIFY_RUNNING, NOTIFY_STATUS = 'ServerStatus.NotifyRunning', 'ServerStatus.NotifyStatus'
    RUNNING_TRUE_FILTER = msgftr.And(msgftr.NameIs(NOTIFY_RUNNING), msgftr.DataEquals(True))
    RUNNING_FALSE_FILTER = msgftr.And(msgftr.NameIs(NOTIFY_RUNNING), msgftr.DataEquals(False))

    UPDATED = 'ServerStatus.Updated'
    UPDATED_FILTER = msgftr.NameIs(UPDATED)


class PlayerStore:
    EVENT = 'PlayerStore.Event'
    EVENT_FILTER = msgftr.NameIs(EVENT)
    EVENT_TRF = msgtrf.DataAsDict()


class ServerProcess:
    STDERR_LINE = 'ServerProcess.StdErrLine'
    STDOUT_LINE = 'ServerProcess.StdOutLine'

    FILTER_STDERR_LINE = msgftr.NameIs(STDERR_LINE)
    FILTER_STDOUT_LINE = msgftr.NameIs(STDOUT_LINE)
    FILTER_ALL_LINES = msgftr.Or(FILTER_STDOUT_LINE, FILTER_STDERR_LINE)

    STATE_START = 'ServerProcess.' + sc.START
    STATE_STARTING = 'ServerProcess.' + sc.STARTING
    STATE_STARTED = 'ServerProcess.' + sc.STARTED
    STATE_STOPPING = 'ServerProcess.' + sc.STOPPING
    STATE_STOPPED = 'ServerProcess.' + sc.STOPPED
    STATE_EXCEPTION = 'ServerProcess.' + sc.EXCEPTION

    FILTER_STATE_STARTED = msgftr.NameIs(STATE_STARTED)
    FILTER_STATE_STOPPING = msgftr.NameIs(STATE_STOPPING)
    FILTER_STATES_UP = msgftr.NameIn((STATE_START, STATE_STARTING, STATE_STARTED, STATE_STOPPING))
    FILTER_STATES_DOWN = msgftr.NameIn((STATE_STOPPED, STATE_EXCEPTION))
    FILTER_STATE_ALL = msgftr.Or(FILTER_STATES_UP, FILTER_STATES_DOWN)
