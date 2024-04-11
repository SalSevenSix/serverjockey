import io
from pympler import muppy, classtracker
from core.msg import msgabc, msgsvc, msgext
from core.context import contextsvc
from core.http import httpabc, httprsc

# https://github.com/pympler/pympler
# https://pympler.readthedocs.io/en/latest/


class MemoryProfilingService:

    def __init__(self, context: contextsvc.Context):
        self._context = context

    def resources(self, resource: httprsc.WebResource):
        if not self._context.config('mprof'):
            return
        r = httprsc.ResourceBuilder(resource)
        r.psh('mprof')
        r.put('all', _AllObjectsHandler())
        # r.put('classes', _ClassTrackerHandler())


class _AllObjectsHandler(httpabc.GetHandler):

    def __init__(self):
        pass

    def handle_get(self, resource, data):
        all_objects = muppy.get_objects()
        result = ['TOTAL: ' + str(len(all_objects))]
        for obj in all_objects:
            if isinstance(obj, msgext.MultiCatcher):
                result.append(str(obj))
        return '\n'.join(result) + '\n'


class _ClassTrackerHandler(httpabc.GetHandler):

    def __init__(self):
        self._text = io.StringIO()
        self._classtracker = classtracker.ClassTracker(self._text)
        self._classtracker.track_class(msgabc.Message)
        self._classtracker.track_class(msgsvc.TaskMailer)
        self._classtracker.track_class(msgext.MultiCatcher)

    def handle_get(self, resource, data):
        try:
            self._classtracker.create_snapshot(compute_total=True)
            self._classtracker.stats.print_summary()
            return self._text.getvalue()
        finally:
            self._classtracker.snapshots = []
            self._text.seek(0)
            self._text.truncate(0)
