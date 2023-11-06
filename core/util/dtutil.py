import time
from datetime import datetime
# ALLOW NONE


def now_millis() -> int:
    return int(time.time() * 1000.0) + 1


def now_datetime() -> datetime:
    return datetime.utcfromtimestamp(time.time())
