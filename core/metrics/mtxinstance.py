from asyncio import subprocess
from prometheus_client import registry
# ALLOW util.* msg*.* context.* metrics.mtxutil
from core.util import signals
from core.msg import msgabc, msgftr
from core.msgc import sc, mc
from core.context import contextsvc
from core.metrics import mtxutil


async def initialise(context: contextsvc.Context, noplayers: bool = False):
    instance_registry = await mtxutil.create_instance_registry()
    context.register(_InstanceCleanup(instance_registry))
    context.register(_InstanceProcessMetrics(context, instance_registry))
    if noplayers:
        return
    subscriber = _InstancePlayerMetrics(context, instance_registry)
    await subscriber.initialise()
    context.register(subscriber)


class _InstanceCleanup(msgabc.AbcSubscriber):

    def __init__(self, instance_registry: registry.CollectorRegistry):
        super().__init__(mc.ServerService.CLEANUP_FILTER)
        self._instance_registry = instance_registry

    async def handle(self, message):
        await mtxutil.unregister_collector(mtxutil.REGISTRY, self._instance_registry)
        return None


class _InstanceProcessMetrics(msgabc.AbcSubscriber):

    def __init__(self, context: contextsvc.Context, instance_registry: registry.CollectorRegistry):
        super().__init__(msgftr.Or(mc.ServerProcess.FILTER_STATE_STARTED, mc.ServerProcess.FILTER_STATES_DOWN))
        self._instance, self._instance_registry = context.config('identity'), instance_registry
        self._collector, self._pid = None, None

    async def handle(self, message):
        if mc.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            process: subprocess.Process = message.data()
            if not process or process.returncode is not None:
                return None
            self._pid = await signals.get_leaf(process.pid)
            if not self._pid:
                return None
            self._collector = await mtxutil.create_process_collector(
                self._instance_registry, self._instance, self._get_pid)
            return None
        if mc.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            if not self._collector:
                return None
            await mtxutil.unregister_collector(self._instance_registry, self._collector)
            self._collector, self._pid = None, None
        return None

    def _get_pid(self):
        return self._pid


class _InstancePlayerMetrics(msgabc.AbcSubscriber):

    def __init__(self, context: contextsvc.Context, instance_registry: registry.CollectorRegistry):
        super().__init__(mc.PlayerStore.EVENT_FILTER)
        self._instance, self._instance_registry = context.config('identity'), instance_registry
        self._player_gauge, self._player_names = None, []

    async def initialise(self):
        self._player_gauge = await mtxutil.create_gauge(self._instance_registry, 'online_players',
                                                        'Number of players connected to the game server')
        await mtxutil.set_gauge(self._player_gauge, self._instance, 0)

    async def handle(self, message):
        data = message.data().asdict()
        event_name = data['event'].upper()
        if event_name == sc.CLEAR:
            if len(self._player_names) > 0:
                await mtxutil.set_gauge(self._player_gauge, self._instance, 0)
                self._player_names = []
            return None
        player_name = data['player']['name']
        if event_name == sc.LOGIN:
            if player_name not in self._player_names:
                self._player_names.append(player_name)
                await mtxutil.set_gauge(self._player_gauge, self._instance, len(self._player_names))
            return None
        if event_name == sc.LOGOUT:
            if player_name in self._player_names:
                self._player_names.remove(player_name)
                await mtxutil.set_gauge(self._player_gauge, self._instance, len(self._player_names))
            return None
        return None
