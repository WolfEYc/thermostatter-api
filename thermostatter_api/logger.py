import logging
from logging import Logger

import colorlog

from thermostatter_api import PROJECT_NAME

log_format = (
    "%(log_color)s%(levelname)s: "
    "%(white)s[%(green)s%(filename)s%(white)s:%(yellow)s%(lineno)d "
    "%(yellow)s%(funcName)s%(white)s()] "
    "%(log_color)s%(message)s"
)


def logger_factory() -> Logger:
    logger = logging.getLogger(PROJECT_NAME)
    color_handler = colorlog.StreamHandler()
    color_handler.setFormatter(colorlog.ColoredFormatter(log_format))
    logger.addHandler(color_handler)
    logger.setLevel(logging.DEBUG)
    return logger


LOGGER = logger_factory()
