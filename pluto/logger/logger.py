#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from logging import getLogger, StreamHandler
from logging.handlers import RotatingFileHandler

from pluto.component.component import PlutoComponent
from pluto.logger.configure import MyFormatter


# The name of the loggers log method (exposed on the system aggregator)
LOG_METHOD = "publish"

# Max size of a log file before it's rotated
ROTATE_LOG_BYTES = 100

# Max depth of log files (i.e. only store the last n rotated log files)
ROTATE_LOG_MAX_DEPTH = 5

# Default log format for logs emitted:
DEFAULT_FORMAT = "[%(asctime)s] %(name)-10s %(levelname)-5s: %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


class PlutoLogger(PlutoComponent):
    """
    The log component is responsible for two things:
        1. Publish log entries for remote viewing
        2. Publish log entries to file (with log rotation)
    """

    class LogEmitter(StreamHandler):
        """
        A logging stream handler which broadcasts log messages
        """

        def __init__(self, broadcast_message):
            super().__init__(stream=self)
            self._broadcast_message = broadcast_message

        def write(self, log_message):
            """
            Called by the Python logger to handle a log message. This handler
            will call the registered broadcast callable to broadcast the
            log entry for any observers to collect.

            :param log_message: The log message to handle
            """
            if log_message == "\n":
                return
            self._broadcast_message(log_message.rstrip("\n"))

        def flush(self):
            """
            Flush the logger
            """
            return

    def __init__(self, eventbus, name="logger", path=None):
        super().__init__(eventbus, name)
        self._root_logger = getLogger()
        self._handlers = []
        self._log_message = ""
        self._handlers.append(self._create_broadcast_logger())
        if path:
            self._handlers.append(self._create_log_rotator(path))
        for handler in self._handlers:
            self._root_logger.addHandler(handler)

    @property
    def log_message(self):
        """
        Holds the latest log message entry, when this value is updated the
        PlutoComponent base class will automatically publish a variable update
        message which means any observers can listen to all log entries
        published by the Pluto system
        """
        return self._log_message

    @log_message.setter
    def log_message(self, message):
        """
        Set the value of the latest log message entry, this will be invoked via
        a lambda function by the "broadcast logger"
        """
        self._log_message = message

    def _create_broadcast_logger(self):
        """
        The "broadcast logger" will set the component variable @log_message
        which will cause log entries to be broadcasted.
        """
        log_emitter = type(self).LogEmitter(
            lambda message: setattr(self, "log_message", message))
        log_emitter.setFormatter(
            MyFormatter(
                colorise=False,
                fmt=DEFAULT_FORMAT,
                datefmt=DEFAULT_DATEFMT))

        return log_emitter

    def _create_log_rotator(self, path):
        """
        Create the "log to file" logger, which is a log rotator which rotates
        log files based on size of log files.

        :Note: an alternative here would be to deploy TimedRotatingFileHandler
        """
        handler = \
            RotatingFileHandler(
                path,
                maxBytes=ROTATE_LOG_BYTES,
                backupCount=ROTATE_LOG_MAX_DEPTH)
        handler.setFormatter(self._root_logger.handlers[0].formatter)
        return handler

    def stop(self):
        """
        Remove the log handlers
        """
        for handler in self._handlers:
            self._root_logger.removeHandler(handler)
