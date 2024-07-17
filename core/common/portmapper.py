import typing
# ALLOW util.* msg*.* context.* http.* system.*
from core.util import util
from core.msg import msgabc, msgftr
from core.msgc import mc
from core.context import contextsvc
from core.remotes import igd


def map_port(mailer: msgabc.Mailer, source: typing.Any, port: int, protocal: str, description: str):
    mailer.post(source, PortMapperService.MAP_PORT, {'port': port, 'protocal': protocal, 'description': description})


class PortMapperService(msgabc.AbcSubscriber):
    MAP_PORT = 'PortMapperService.MapPort'
    MAP_PORT_FILTER = msgftr.NameIs(MAP_PORT)

    def __init__(self, context: contextsvc.Context):
        super().__init__(msgftr.Or(
            mc.ServerService.CLEANUP_FILTER,
            mc.ServerStatus.RUNNING_FALSE_FILTER,
            mc.ServerProcess.FILTER_STATE_STARTED,
            PortMapperService.MAP_PORT_FILTER))
        self._root_context = context.root()
        self._active, self._trash = [], []

    def handle(self, message):
        if mc.ServerService.CLEANUP_FILTER.accepts(message):
            self._trash.extend(self._active)
            self._delete_trash()
            return True
        if mc.ServerStatus.RUNNING_FALSE_FILTER.accepts(message):
            self._trash.extend(self._active)
            self._active = []
            return None
        if mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            self._delete_trash()
            return None
        if PortMapperService.MAP_PORT_FILTER.accepts(message):
            data = message.data()
            port, protocal = util.get('port', data), util.get('protocal', data)
            signature = {'port': port, 'protocal': protocal}
            self._active.append(signature)
            if signature in self._trash:
                self._trash.remove(signature)
            else:
                description = util.get('description', data)
                igd.add_port_mapping(self._root_context, message.source(), port, protocal, description)
            return None
        return None

    def _delete_trash(self):
        for signature in self._trash:
            port, protocal = util.get('port', signature), util.get('protocal', signature)
            igd.delete_port_mapping(self._root_context, self, port, protocal)
        self._trash = []
