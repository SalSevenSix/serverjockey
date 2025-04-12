import logging
# ALLOW util.util


def prev_logname(logname: str) -> str:
    return logname[:-4] + '_prev.log' if logname.endswith('.log') else logname + '.prev'


def is_logging_to_file() -> bool:
    for handler in logging.getLogger().handlers:
        # pylint: disable=unidiomatic-typecheck
        if type(handler) is logging.FileHandler:
            return True
    return False


def is_logging_to_stream() -> bool:
    for handler in logging.getLogger().handlers:
        # pylint: disable=unidiomatic-typecheck
        if type(handler) is logging.StreamHandler:
            return True
    return False
