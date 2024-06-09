import logging
import typing
from prometheus_client import metrics_core, metrics, registry
# ALLOW util.*
from core.util import funcutil
from core.metrics import mtxutil


# Uses blocking IO because it must
class _ProcessCollector(registry.Collector):

    def __init__(self, instance: str, pid: int | None = None):
        self._instance, self._pid = instance, pid

    def collect(self) -> typing.Iterable[metrics.Metric]:
        result = []
        try:
            result.extend(self._collect_io_metrics())
        except Exception as e:
            logging.debug('collect_io_metrics() ' + str(e))
        return result

    def _collect_io_metrics(self) -> list:
        result = []
        for line in self._read_proc('io').strip().split('\n'):
            if line.startswith('read_bytes:'):
                metric = metrics_core.CounterMetricFamily(
                    'process_read_bytes', 'Total bytes read from storage by process',
                    labels=[mtxutil.PROC_LABEL_KEY], unit='bytes')
                metric.add_metric([self._instance], float(line[11:].strip()))
                result.append(metric)
            elif line.startswith('write_bytes:'):
                metric = metrics_core.CounterMetricFamily(
                    'process_write_bytes', 'Total bytes written to storage by process',
                    labels=[mtxutil.PROC_LABEL_KEY], unit='bytes')
                metric.add_metric([self._instance], float(line[12:].strip()))
                result.append(metric)
        return result

    def _read_proc(self, filename) -> str:
        pid = str(self._pid) if self._pid else 'self'
        with open('/proc/' + pid + '/' + filename, 'rt') as file:
            return file.read()


def _sync_create_process_collector(
        a_registry: registry.CollectorRegistry,
        instance: str, pid: int | None = None) -> typing.Optional[registry.Collector]:
    try:
        collector = _ProcessCollector(instance, pid)
        a_registry.register(collector)
        return collector
    except Exception as e:
        logging.debug('mtxproc.create_process_collector() ' + str(e))
    return None


_sync_create_process_collector(mtxutil.REGISTRY, mtxutil.PROC_LABEL_VALUE_SELF)
create_process_collector = funcutil.to_async(_sync_create_process_collector)
