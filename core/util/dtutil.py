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


def human_duration(seconds: float, parts: int = 3) -> str:
    value = seconds if seconds and seconds > 0.0 else 0.0
    days, hours = -1, -1
    if parts > 2:
        days = math.floor(value / 86400.0)
        value -= days * 86400.0
    if parts > 1:
        hours = math.floor(value / 3600.0)
        value -= hours * 3600.0
    result = ''
    if days > -1:
        result += str(days) + 'd '
    if hours > -1:
        result += str(hours) + 'h '
    result += str(math.floor(value / 60.0)) + 'm'
    return result
