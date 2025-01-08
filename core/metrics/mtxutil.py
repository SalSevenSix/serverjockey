import logging
import typing
import prometheus_client
from prometheus_client import metrics, registry
# ALLOW util.*
from core.util import funcutil


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
PROC_LABEL_KEY, PROC_LABEL_VALUE_SELF = 'process', 'serverjockey'
REGISTRY = registry.CollectorRegistry()
REGISTRY.register(_AppendLabelsCollector(prometheus_client.REGISTRY, {PROC_LABEL_KEY: PROC_LABEL_VALUE_SELF}))


def _sync_create_process_collector(
        instance_registry: registry.CollectorRegistry, instance: str,
        get_pid: typing.Callable) -> typing.Optional[registry.Collector]:
    try:
        collector = prometheus_client.process_collector.ProcessCollector(pid=get_pid, registry=None)
        collector = _AppendLabelsCollector(collector, {PROC_LABEL_KEY: instance})
        instance_registry.register(collector)
        return collector
    except Exception as e:
        logging.debug('mtxutil.create_process_collector() %s', repr(e))
    return None


def _sync_create_instance_registry() -> registry.CollectorRegistry:
    instance_registry = registry.CollectorRegistry()
    REGISTRY.register(instance_registry)
    return instance_registry


def _sync_unregister_collector(a_registry: registry.CollectorRegistry, collector: registry.Collector):
    if not collector:
        return
    try:
        a_registry.unregister(collector)
    except Exception as e:
        logging.warning('mtxutil.unregister_collector() %s', repr(e))


def _sync_create_gauge(a_registry: registry.CollectorRegistry, name: str,
                       documentation: str, labelnames: iter = None) -> metrics.Gauge:
    allnames = [PROC_LABEL_KEY]
    if labelnames:
        allnames.extend(labelnames)
    return metrics.Gauge(name, documentation, labelnames=allnames, registry=a_registry)


def _sync_set_gauge(gauge: metrics.Gauge, instance: str, value: float, labelvalues: iter = None):
    allvalues = [instance]
    if labelvalues:
        allvalues.extend(labelvalues)
    gauge.labels(*allvalues).set(value)


def _sync_create_counter(a_registry: registry.CollectorRegistry, name: str, documentation: str) -> metrics.Counter:
    return metrics.Counter(name, documentation, labelnames=[PROC_LABEL_KEY], registry=a_registry)


def _sync_reset_counter(counter: metrics.Counter, instance: str):
    counter.labels(instance).reset()


def _sync_inc_counter(counter: metrics.Counter, instance: str, amount: float = 1):
    counter.labels(instance).inc(amount)


create_process_collector = funcutil.to_async(_sync_create_process_collector)
create_instance_registry = funcutil.to_async(_sync_create_instance_registry)
unregister_collector = funcutil.to_async(_sync_unregister_collector)
create_gauge = funcutil.to_async(_sync_create_gauge)
set_gauge = funcutil.to_async(_sync_set_gauge)
create_counter = funcutil.to_async(_sync_create_counter)
reset_counter = funcutil.to_async(_sync_reset_counter)
inc_counter = funcutil.to_async(_sync_inc_counter)
