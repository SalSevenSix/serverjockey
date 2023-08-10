import logging
# ALLOW util.util


def prev_logname(logname: str) -> str:
    return logname[:-4] + '_prev.log' if logname.endswith('.log') else logname + '.prev'


def is_logging_to_file() -> bool:
    for handler in logging.getLogger().handlers:
        if type(handler) is logging.FileHandler:
            return True
    return False


def is_logging_to_stream() -> bool:
    for handler in logging.getLogger().handlers:
        if type(handler) is logging.StreamHandler:
            return True
    return False


def get_level() -> int:
    return logging.getLogger().level


def get_formatter() -> logging.Formatter | None:
    for handler in logging.getLogger().handlers:
        if handler.formatter:
            return handler.formatter
    return None


class NullLogger:

    def log(self, level, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def fatal(self, msg, *args, **kwargs):
        pass
