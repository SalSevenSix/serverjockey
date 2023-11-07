import time
# ALLOW NONE


def now_millis() -> int:
    return int(time.time() * 1000.0)


def format_time(ft: str, seconds: float, local: bool = True) -> str:
    value = time.localtime(seconds) if local else time.gmtime(seconds)
    return time.strftime(ft, value)


def format_time_standard(seconds: float, local: bool = True) -> str:
    return format_time('%Y-%m-%d %H:%M:%S', seconds, local)
