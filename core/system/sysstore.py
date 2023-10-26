import typing
# TODO ALLOW ???
from core.util import util, objconv
from core.msg import msgabc, msgftr
from core.context import contextsvc
from core.system import system, svrsvc
from core.common import playerstore  # TODO no No NO!
from core.store import storeabc, storetxn, storesvc


def initialise(context: contextsvc.Context, source: typing.Any):
    context.register(storesvc.StoreService(context))
    context.post(source, storesvc.StoreService.INITIALISE)
    context.register(_SystemRouting(context))


class _SystemRouting(msgabc.AbcSubscriber):

    def __init__(self, mailer: msgabc.Mailer):
        super().__init__(system.SystemService.SERVER_FILTER)
        self._mailer = mailer

    async def handle(self, message):
        source, name, data = message.source(), message.name(), message.data()
        if name is system.SystemService.SERVER_INITIALISED:
            storeabc.execute(self._mailer, source, storetxn.InsertInstance(data))
            return None
        if name is system.SystemService.SERVER_DELETED:
            storeabc.execute(self._mailer, source, storetxn.DeleteInstance(data))
            return None
        return None


class InstanceRouting(msgabc.AbcSubscriber):
    _LOGIN, _LOGOUT, _CLEAR, _CHAT = 'LOGIN', 'LOGOUT', 'CLEAR', 'CHAT'

    def __init__(self, subcontext: contextsvc.Context):
        super().__init__(msgftr.Or(
            svrsvc.ServerStatus.UPDATED_FILTER,
            playerstore.EVENT_FILTER))
        self._subcontext, self._mailer = subcontext, subcontext.root()
        self._last_state, self._player_names = 'READY', set()

    async def handle(self, message):
        source, data = message.source(), message.data()
        if svrsvc.ServerStatus.UPDATED_FILTER.accepts(message):
            state = util.get('state', data)
            if state == self._last_state:
                return None
            self._last_state = state
            details = objconv.obj_to_json(util.get('details', data))
            storeabc.execute(self._mailer, source, storetxn.InsertInstanceEvent(self._subcontext, state, details))
            return None
        if playerstore.EVENT_FILTER.accepts(message):
            event = data.asdict()
            event_name = event['event'].upper()
            if event_name == InstanceRouting._CLEAR:
                for player_name in self._player_names:
                    storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                        self._subcontext, InstanceRouting._LOGOUT, player_name, None))
                self._player_names = set()
                return None
            player_name = event['player']['name']
            if event_name == InstanceRouting._CHAT:
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerChat(
                    self._subcontext, player_name, event['text']))
                return None
            steamid = event['player']['steamid']
            if event_name == InstanceRouting._LOGIN:
                self._player_names.add(player_name)
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                    self._subcontext, event_name, player_name, steamid))
                return None
            if event_name == InstanceRouting._LOGOUT:
                self._player_names.remove(player_name)
                storeabc.execute(self._mailer, source, storetxn.InsertPlayerEvent(
                    self._subcontext, event_name, player_name, steamid))
                return None
            return None
