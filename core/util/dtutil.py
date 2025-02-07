import time
import math
# ALLOW NONE


def to_seconds(millis: int) -> float:
    return float(millis) / 1000.0


def to_millis(seconds: float) -> int:
    return int(seconds * 1000.0)


def now_millis() -> int:
    return to_millis(time.time())


def format_time(ft: str, seconds: float, local: bool = True) -> str:
    value = time.localtime(seconds) if local else time.gmtime(seconds)
    return time.strftime(ft, value)


def format_time_standard(seconds: float, local: bool = True) -> str:
    return format_time('%Y-%m-%d %H:%M:%S', seconds, local)


def format_timezone_standard(seconds: float) -> str:
    data = duration_to_dict(seconds, 'hm')
    hh, mm = data['h'], data['m']
    op = '-' if hh < 0 or mm < 0 else '+'
    hh, mm = hh if hh > 0 else 0 - hh, mm if mm > 0 else 0 - mm
    hh, mm = str(hh).rjust(2, '0'), str(mm).rjust(2, '0')
    return op + hh + ':' + mm


def duration_to_dict(seconds: float, parts: str = 'dhm') -> dict:
    result, remainder = {}, seconds if seconds else 0.0
    for key, value in dict(d=86400.0, h=3600.0, m=60.0, s=1.0).items():
        if parts.find(key) != -1:
            result[key] = math.floor(remainder / value) if remainder > 0 else math.ceil(remainder / value)
            remainder -= result[key] * value
    return result


def duration_to_str(seconds: float, parts: str = 'dhm') -> str:
    result = []
    for key, value in duration_to_dict(seconds, parts).items():
        result.append(str(value) + key)
    return ' '.join(result)
