import logging
import typing
import prometheus_client
from prometheus_client import metrics, registry
# ALLOW util.* msg*.* context.* http.*
from core.util import funcutil, signals
from core.msg import msgabc, msgftr
from core.msgc import sc, mc
from core.context import contextsvc
from core.http import httpabc, httpcnt, httpsec
# TODO imports below not allowed
from core.system import svrsvc
from core.proc import proch


class _AppendLabelsCollector(registry.Collector):

    def __init__(self, delegate: registry.Collector, labels: typing.Dict[str, str]):
        self._delegate, self._labels = delegate, labels

    def collect(self) -> typing.Iterable[metrics.Metric]:
        results = []
        for om in self._delegate.collect():
            metric = metrics.Metric(om.name, om.documentation, om.type, om.unit)
            for os in om.samples:
                labels = os.labels.copy() if os.labels else {}
                labels.update(self._labels)
                metric.add_sample(os.name, labels, os.value, os.timestamp, os.exemplar)
            results.append(metric)
        return results


prometheus_client.disable_created_metrics()
_INSTANCE_LABEL = 'sjgms_instance'
_REGISTRY = registry.CollectorRegistry()
_REGISTRY.register(_AppendLabelsCollector(prometheus_client.REGISTRY, {_INSTANCE_LABEL: 'serverjockey'}))


def _sync_register_process_collector(
        instance_registry: registry.CollectorRegistry, instance: str,
        get_pid: typing.Callable) -> typing.Optional[registry.Collector]:
    try:
        collector = prometheus_client.process_collector.ProcessCollector(pid=get_pid, registry=None)
        collector = _AppendLabelsCollector(collector, {_INSTANCE_LABEL: instance})
        instance_registry.register(collector)
        return collector
    except Exception as e:
        logging.debug('_register_process_collector() ' + str(e))
    return None


def _sync_new_instance_registry() -> registry.CollectorRegistry:
    instance_registry = registry.CollectorRegistry()
    _REGISTRY.register(instance_registry)
    return instance_registry


def _sync_unregister_collector(a_registry: registry.CollectorRegistry, collector: registry.Collector):
    try:
        a_registry.unregister(collector)
    except Exception as e:
        logging.warning('_unregister_collector()' + str(e))


def _sync_new_gauge(instance_registry: registry.CollectorRegistry, name: str, documentation: str) -> metrics.Gauge:
    return metrics.Gauge(name, documentation, labelnames=[_INSTANCE_LABEL], registry=instance_registry)


def _sync_set_gauge(gauge: metrics.Gauge, instance: str, value: float, inc: bool = None):
    metric = gauge.labels(instance)
    if inc is True:
        metric.inc(value)
    elif inc is False:
        metric.dec(value)
    else:
        metric.set(value)


_register_process_collector = funcutil.to_async(_sync_register_process_collector)
_new_instance_registry = funcutil.to_async(_sync_new_instance_registry)
_unregister_collector = funcutil.to_async(_sync_unregister_collector)
_new_gauge = funcutil.to_async(_sync_new_gauge)
_set_gauge = funcutil.to_async(_sync_set_gauge)


# TODO possibly call from instance... player metrics not always applicable
async def initialise_instance(subcontext: contextsvc.Context):
    instance_registry = await _new_instance_registry()
    subcontext.register(_InstanceCleanup(instance_registry))
    subcontext.register(_InstanceProcessMetrics(subcontext, instance_registry))
    subscriber = _InstancePlayerMetrics(subcontext, instance_registry)
    await subscriber.initialise()
    subcontext.register(subscriber)


class _InstanceProcessMetrics(msgabc.AbcSubscriber):

    def __init__(self, subcontext: contextsvc.Context, instance_registry: registry.CollectorRegistry):
        super().__init__(msgftr.Or(proch.ServerProcess.FILTER_STATE_STARTED, proch.ServerProcess.FILTER_STATES_DOWN))
        self._instance, self._instance_registry = subcontext.config('identity'), instance_registry
        self._collector, self._pid = None, None

    async def handle(self, message):
        if proch.ServerProcess.FILTER_STATE_STARTED.accepts(message):
            process = message.data()
            if not process or process.returncode is not None:
                return None
            self._pid = await signals.get_leaf(process.pid)
            if not self._pid:
                return None
            self._collector = await _register_process_collector(self._instance_registry, self._instance, self._get_pid)
            return None
        if proch.ServerProcess.FILTER_STATES_DOWN.accepts(message):
            if not self._collector:
                return None
            await _unregister_collector(self._instance_registry, self._collector)
            self._collector, self._pid = None, None
        return None

    def _get_pid(self):
        return self._pid


class _InstancePlayerMetrics(msgabc.AbcSubscriber):

    def __init__(self, subcontext: contextsvc.Context, instance_registry: registry.CollectorRegistry):
        super().__init__(mc.PlayerStore.EVENT_FILTER)
        self._instance, self._instance_registry = subcontext.config('identity'), instance_registry
        self._player_gauge, self._player_names = None, []

    async def initialise(self):
        self._player_gauge = await _new_gauge(self._instance_registry, 'online_players',
                                              'Number of players connected to the game server')
        await _set_gauge(self._player_gauge, self._instance, 0)

    async def handle(self, message):
        data = message.data().asdict()
        event_name = data['event'].upper()
        if event_name == sc.CLEAR:
            if len(self._player_names) > 0:
                await _set_gauge(self._player_gauge, self._instance, 0)
                self._player_names = []
            return None
        player_name = data['player']['name']
        if event_name == sc.LOGIN:
            if player_name not in self._player_names:
                self._player_names.append(player_name)
                await _set_gauge(self._player_gauge, self._instance, len(self._player_names))
            return None
        if event_name == sc.LOGOUT:
            if player_name in self._player_names:
                self._player_names.remove(player_name)
                await _set_gauge(self._player_gauge, self._instance, len(self._player_names))
            return None
        return None


class _InstanceCleanup(msgabc.AbcSubscriber):

    def __init__(self, instance_registry: registry.CollectorRegistry):
        super().__init__(svrsvc.ServerService.CLEANUP_FILTER)
        self._instance_registry = instance_registry

    async def handle(self, message):
        await _unregister_collector(_REGISTRY, self._instance_registry)
        return None


_CONTENT_TYPE_LATEST = httpcnt.ContentTypeImpl(prometheus_client.CONTENT_TYPE_LATEST)
_generate_latest = funcutil.to_async(prometheus_client.generate_latest)


class MetricsHandler(httpabc.GetHandler):

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        body = await _generate_latest(_REGISTRY)
        return httpabc.ResponseBody(body, _CONTENT_TYPE_LATEST)
