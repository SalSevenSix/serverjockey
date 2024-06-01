import time
# ALLOW util.*


# TODO Unused
class CacheDict:

    def __init__(self, stale: float = 86400.0, freq: int = 10):
        assert stale >= 0.0
        assert freq >= 0
        self._stale, self._freq = stale, freq
        self._count, self._data = 0, {}

    def get(self, key: any) -> any:
        cached = self._data.get(key)
        if cached is None:
            return None
        now = time.time()
        cached.at = now
        self._count += 1
        if self._count > self._freq:
            self._cleanup(now)
            self._count = 0
        print('GET ' + str(len(self._data)))
        return cached.value

    def set(self, key: any, value: any):
        assert key is not None
        assert value is not None
        self._data[key] = _CacheDictValue(value)
        print('SET ' + str(len(self._data)))

    def _cleanup(self, now: float):
        stales = []
        for key, value in self._data.items():
            if now - value.at > self._stale:
                stales.append(key)
        for key in stales:
            del self._data[key]


class _CacheDictValue:

    def __init__(self, value: any):
        self.at, self.value = time.time(), value
