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
