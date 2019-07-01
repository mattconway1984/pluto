#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from logging import basicConfig
from sys import stdout


LOGGER_CONFIG_FORMAT = "[%(asctime)s] [%(name)s] %(levelname)-5s: %(message)s"
LOGGER_CONFIG_DATEFMT = "%Y-%m-%d %H:%M:%S"
LOGGER_CONFIG_STREAM = stdout


def configure_logger(log_threshold):
    """
    Configure the Python logger

    :param log_threshold: Logging threshold level (minimum logging level)
    """
    basicConfig(
        level=log_threshold,
        format=LOGGER_CONFIG_FORMAT,
        datefmt=LOGGER_CONFIG_DATEFMT,
        stream=LOGGER_CONFIG_STREAM
    )
