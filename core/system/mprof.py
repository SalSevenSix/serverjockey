import collections
from pympler import muppy
# ALLOW util.* http.*
from core.http import httpabc, httpcnt

# https://github.com/pympler/pympler
# https://pympler.readthedocs.io/en/latest/

_BASIC_TYPES = ('int', 'float', 'str', 'dict', 'list', 'bytes')


class MemoryProfilingHandler(httpabc.GetHandler):

    def __init__(self):
        self._captures = collections.deque()

    def handle_get(self, resource, data):
        if not httpcnt.is_secure(data):
            return httpabc.ResponseBody.UNAUTHORISED
        while len(self._captures) >= 26:
            self._captures.pop()
        self._captures.appendleft(_generate_capture())
        entries = _generate_entries(self._captures)
        results = _generate_results(entries)
        return 'CLASS'.ljust(32) + ',  COUNT,   ~,' \
            + '  01,  02,  03,  04,  05,  06,  07,  08,  09,  10,' \
            + '  11,  12,  13,  14,  15,  16,  17,  18,  19,  20,' \
            + '  21,  22,  23,  24,  25\n' + '\n'.join(results) + '\n'


def _generate_capture() -> dict:
    all_objects = muppy.get_objects()
    capture = {'TOTAL': len(all_objects)}
    for obj in filter(_filter_objects, all_objects):
        classname = obj.__class__.__name__
        if classname in capture:
            capture[classname] += 1
        else:
            capture[classname] = 1
    return capture


def _generate_entries(captures: iter) -> tuple:
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


def _generate_results(entries: tuple) -> tuple:
    results = []
    for entry in filter(_filter_entries, entries):
        classname, count, deltas = entry['classname'], entry['count'], entry['deltas']
        line, dsum = '', 0
        for delta in deltas:
            line += ',' + str(delta).rjust(4)
            dsum += delta
        results.append(classname.ljust(32) + ',' + str(count).rjust(7) + ',' + str(dsum).rjust(4) + line)
    return tuple(results)


def _sort_entries(entry) -> int:
    return entry['count']


def _filter_objects(obj) -> bool:
    if obj.__class__.__name__ in _BASIC_TYPES:
        return True
    modulename = obj.__class__.__module__
    return modulename.startswith('core.') or modulename.startswith('servers.')


def _filter_entries(entry) -> bool:
    classname, deltas = entry['classname'], entry['deltas']
    if classname == 'TOTAL' or len(deltas) == 0:
        return True
    for delta in deltas:
        if delta != 0:
            return True
    return False
