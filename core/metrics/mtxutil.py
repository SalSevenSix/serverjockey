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
_LABEL_KEY = 'process'
REGISTRY = registry.CollectorRegistry()
REGISTRY.register(_AppendLabelsCollector(prometheus_client.REGISTRY, {_LABEL_KEY: 'serverjockey'}))


def _sync_create_process_collector(
        instance_registry: registry.CollectorRegistry, instance: str,
        get_pid: typing.Callable) -> typing.Optional[registry.Collector]:
    try:
        collector = prometheus_client.process_collector.ProcessCollector(pid=get_pid, registry=None)
        collector = _AppendLabelsCollector(collector, {_LABEL_KEY: instance})
        instance_registry.register(collector)
        return collector
    except Exception as e:
        logging.debug('_register_process_collector() ' + str(e))
    return None


def _sync_create_instance_registry() -> registry.CollectorRegistry:
    instance_registry = registry.CollectorRegistry()
    REGISTRY.register(instance_registry)
    return instance_registry


def _sync_unregister_collector(a_registry: registry.CollectorRegistry, collector: registry.Collector):
    try:
        a_registry.unregister(collector)
    except Exception as e:
        logging.warning('_unregister_collector()' + str(e))


def _sync_create_gauge(instance_registry: registry.CollectorRegistry, name: str, documentation: str) -> metrics.Gauge:
    return metrics.Gauge(name, documentation, labelnames=[_LABEL_KEY], registry=instance_registry)


def _sync_set_gauge(gauge: metrics.Gauge, instance: str, value: float, inc: bool = None):
    metric = gauge.labels(instance)
    if inc is True:
        metric.inc(value)
    elif inc is False:
        metric.dec(value)
    else:
        metric.set(value)


create_process_collector = funcutil.to_async(_sync_create_process_collector)
create_instance_registry = funcutil.to_async(_sync_create_instance_registry)
unregister_collector = funcutil.to_async(_sync_unregister_collector)
create_gauge = funcutil.to_async(_sync_create_gauge)
set_gauge = funcutil.to_async(_sync_set_gauge)
