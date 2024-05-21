import time
# ALLOW const.*


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
