import logging


def is_logging_to_file(logger: logging.Logger) -> bool:
    for handler in logger.handlers:
        if type(handler) is logging.FileHandler:
            return True
    return False


def is_logging_to_stream(logger: logging.Logger) -> bool:
    for handler in logger.handlers:
        if type(handler) is logging.StreamHandler:
            return True
    return False


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
