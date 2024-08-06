import collections
import gc
# ALLOW util.* http.*
from core.http import httpabc, httpsec
from core.metrics import mtxutil

# https://github.com/pympler/pympler
# https://pympler.readthedocs.io/en/latest/
# TODO switched from using pympler to bad custom solution because issues on python3.12

_TOTAL = 'TOTAL'
_BASIC_TYPES = (int, float, str, dict, set, tuple, list, bytes)


class MemoryProfilingHandler(httpabc.GetHandler):

    def __init__(self):
        self._captures, self._objcount_gauge = None, None

    async def handle_get(self, resource, data):
        if not httpsec.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        if self._captures:
            while len(self._captures) >= 26:
                self._captures.pop()
        else:  # Lazy init
            self._captures = collections.deque()
            self._objcount_gauge = await mtxutil.create_gauge(mtxutil.REGISTRY, 'python_all_objects',
                                                              'Count of all python objects in memory')
        result = _generate_capture()
        await mtxutil.set_gauge(self._objcount_gauge, mtxutil.PROC_LABEL_VALUE_SELF, result[_TOTAL])
        self._captures.appendleft(result)
        result = _process_captures(self._captures)
        result = _build_report(result)
        return _format_report(result)


def _generate_capture() -> dict:
    all_objects = _get_all_objects()
    capture = {_TOTAL: len(all_objects)}
    for obj in all_objects:
        classname = obj.__class__.__name__
        if classname in capture:
            capture[classname] += 1
        else:
            capture[classname] = 1
    return capture


def _process_captures(captures: iter) -> tuple:
    unique_classnames = set()
    for capture in captures:
        unique_classnames.update(capture.keys())
    entries, unique_classnames = [], tuple(unique_classnames)
    for classname in unique_classnames:
        entry, pc, count = {'classname': None, 'count': 0, 'deltas': []}, 0, 0
        for capture in captures:
            pc, count = count, capture[classname] if classname in capture else 0
            if entry['classname']:
                entry['deltas'].append(pc - count)
            else:
                entry['classname'], entry['count'] = classname, count
        entries.append(entry)
    entries.sort(key=_sort_entries, reverse=True)
    return tuple(entries)


def _build_report(entries: tuple) -> tuple:
    results = []
    for entry in filter(_filter_entries, entries):
        classname, count, deltas = entry['classname'], entry['count'], entry['deltas']
        line, dsum = '', 0
        for delta in deltas:
            line += ',' + str(delta).rjust(4)
            dsum += delta
        results.append(classname.ljust(32) + ',' + str(count).rjust(7) + ',' + str(dsum).rjust(4) + line)
    return tuple(results)


def _format_report(report: iter) -> str:
    return 'CLASS'.ljust(32) + ',  COUNT,   ~,' \
        + '  01,  02,  03,  04,  05,  06,  07,  08,  09,  10,' \
        + '  11,  12,  13,  14,  15,  16,  17,  18,  19,  20,' \
        + '  21,  22,  23,  24,  25\n' + '\n'.join(report) + '\n'


def _sort_entries(entry) -> int:
    return entry['count']


def _filter_entries(entry) -> bool:
    classname, deltas = entry['classname'], entry['deltas']
    if classname == _TOTAL or len(deltas) == 0:
        return True
    for delta in deltas:
        if delta != 0:
            return True
    return False


def _filter_objects(obj) -> bool:
    if obj.__class__ in _BASIC_TYPES:
        return True
    modulename = obj.__class__.__module__
    return modulename.startswith('core.') or modulename.startswith('servers.')


def _getr(slist, olist, seen):
    for o in slist:
        oid = id(o)
        if oid not in seen and _filter_objects(o):
            seen[oid] = None
            olist.append(o)
            tl = gc.get_referents(o)
            if tl:
                _getr(tl, olist, seen)


def _get_all_objects():
    gcl, seen, olist = gc.get_objects(), {}, []
    seen[id(gcl)], seen[id(seen)], seen[id(olist)] = None, None, None
    _getr(gcl, olist, seen)
    return olist
