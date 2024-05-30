# ALLOW util.* msg.msgftr msg.msgtrf
from core.msg import msgftr, msgtrf


class SystemService:
    SERVER_INITIALISED = 'SystemService.ServerInitialised'
    SERVER_DELETED = 'SystemService.ServerDestroyed'
    SERVER_FILTER = msgftr.NameIn((SERVER_INITIALISED, SERVER_DELETED))


class ServerStatus:
    UPDATED = 'ServerStatus.Updated'
    UPDATED_FILTER = msgftr.NameIs(UPDATED)


class PlayerStore:
    EVENT = 'PlayerStore.Event'
    EVENT_FILTER = msgftr.NameIs(EVENT)
    EVENT_TRF = msgtrf.DataAsDict()
