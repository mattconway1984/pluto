#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

import io
import logging
import sys
from logging.handlers import RotatingFileHandler

DEFAULT_FORMAT = "[%(asctime)s] %(name)-10s %(levelname)-5s: %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = logging.DEBUG
DEFAULT_LOGFILE = ""
DEFAULT_STREAM = sys.stdout
DEFAULT_ROTATE_SIZE_BYTES = 10*1024*1024 # 10Mib
DEFAULT_ROTATE_MAX_DEPTH = 5

# Specify values for the custom log levels
LOG_TRACE_LEVEL = 9
LOG_NOTICE_LEVEL = 21
LOG_PROMPT_LEVEL = 222


class Colors:
    """
    Defines ANSI escape codes that add colour to output.
    """
    #pylint:disable=too-few-public-methods

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37


class MyFormatter(logging.Formatter):
    """
    A log formatter with the option to colorise log entries using ANSI escape
    codes.

    Args:
        colorise (bool): True if the logging formatter should apply colors
            to the log messages (not recommended when directing to logfiles).
    """

    # Map logging.LEVEL to a colour:
    _COLOR_MAP = {
        "TRACE": Colors.GREEN,
        "DEBUG": Colors.CYAN,
        "INFO": Colors.BLUE,
        "NOTICE": Colors.YELLOW,
        "PROMPT": Colors.RED,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.MAGENTA,
        "CRITICAL": Colors.RED,
    }

    # ANSI escape codes that format output:
    _ESCAPE_CODE = {
        "COLOR": "\033[%dm",
        "RESET": "\u001b[0m",
        "BOLD": "\033[1m",
    }

    def __init__(self, colorise=False, **kwargs):
        self._colorise = colorise
        super().__init__(**kwargs)

    def format(self, record):
        #pylint:disable=no-member
        if self._colorise:
            color = type(self)._COLOR_MAP.get(record.levelname)
            if color:
                record.levelname = "{}{}{}{}".format(
                    type(self)._ESCAPE_CODE["COLOR"] % color,
                    type(self)._ESCAPE_CODE["BOLD"],
                    record.levelname,
                    type(self)._ESCAPE_CODE["RESET"])
                # Colorise the message part of the custom log levels:
                if (
                        record.levelno == logging.TRACE or
                        record.levelno == logging.NOTICE or
                        record.levelno == logging.PROMPT):
                    record.msg = "{}{}{}".format(
                        type(self)._ESCAPE_CODE["COLOR"] % color,
                        record.msg,
                        type(self)._ESCAPE_CODE["RESET"])
        return logging.Formatter.format(self, record)


def configure_logger(
        level: int = DEFAULT_LEVEL,
        fmt: str = DEFAULT_FORMAT,
        datefmt: str = DEFAULT_DATEFMT,
        logfile: str = DEFAULT_LOGFILE,
        stream: io.TextIOWrapper = DEFAULT_STREAM):
    """
    Configure the Python logger.

    Args:
        level (int): Specify the minimum log level for messages emitted
            by the logger.
        fmt (str): Use the specified format string for the log messages.
        datefmt (str): Use the specified date/time format, as accepted by
            `time.strftime()`.
        logfile (str): If specified, a rotating log file handler will be
            created, and log messages will be emitted to the specified
            logfile. Once files have grown to 10Mib (default value) they
            shall be rotated, a maximum of 5 historic logfiles will be kept
            (default value)
        stream (str): If specified, indicates the output stream to which log
            messages shall be emitted.
    """
    _configure_custom_log_levels()
    root = logging.getLogger("")
    root.setLevel(level)
    if logfile:
        _configure_logfile_handler(root, logfile, fmt, datefmt)
    if stream:
        _configure_stream_handler(root, stream, fmt, datefmt)


def add_log_level(name: str, level: int, fname: str = None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class. This method will avoid accidental
    clobberings of existing logging levels, refer to Exceptions.

    Args:
        name (str): Name of the log level to add.
        level (int): Value of the log level to add.
        fname (str): Name of the logging function to assign for this log level.


    Example:
        `fname` will be added to the logger as a convenience method for both
        `logging` itself and the class returned by `logging.getLoggerClass()`
        (usually just `logging.Logger`). If `fname` is not specified,
        `levelName.lower()` is used. Usage example:

            .. highlight: Python
            .. code-block: Python

                add_log_level("FOO", 15, "logfoo")

                import logging
                logger = logging.getLogger("My Logger")
                logger.logfoo("a log message with log level `FOO`")
                logging.logfoo("another log message with log level `FOO`")
                assert logging.FOO == 15, "logging.FOO is not as expected"

    Raises:
        AttributeError: If the level name is already an attribute of the
            `logging` module or if the method name is already present
    """
    if fname is None:
        fname = name.lower()
    if hasattr(logging, name):
        raise AttributeError('Log level `{}` already exists'.format(name))
    if hasattr(logging, fname):
        raise AttributeError('Log function `{}` already exists'.format(fname))
    if hasattr(logging.getLoggerClass(), fname):
        raise AttributeError('Log function `{}` already exists'.format(fname))

    def _log_for_level(self, message, *args, **kwargs):
        #pylint:disable=protected-access
        if self.isEnabledFor(level):
            # Note: _log() takes '*args' as 'args'
            self._log(level, message, args, **kwargs)

    def _log_to_root(message, *args, **kwargs):
        logging.log(level, message, *args, **kwargs)

    logging.addLevelName(level, name)
    setattr(logging, name, level)
    setattr(logging, fname, _log_to_root)
    setattr(logging.getLoggerClass(), fname, _log_for_level)


def _configure_custom_log_levels():
    add_log_level("TRACE", LOG_TRACE_LEVEL)
    add_log_level("NOTICE", LOG_NOTICE_LEVEL)
    add_log_level("PROMPT", LOG_PROMPT_LEVEL)


def _configure_stream_handler(root, stream, fmt, datefmt):
    console_stream = logging.StreamHandler(stream=stream)
    console_stream.setFormatter(
        MyFormatter(
            colorise=True,
            fmt=fmt,
            datefmt=datefmt))
    root.addHandler(console_stream)


def _configure_logfile_handler(root, logfile, fmt, datefmt):
    logfile_handler = \
        RotatingFileHandler(
            logfile,
            maxBytes=DEFAULT_ROTATE_SIZE_BYTES,
            backupCount=DEFAULT_ROTATE_MAX_DEPTH)
    logfile_handler.setFormatter(
        MyFormatter(
            colorise=False,
            fmt=fmt,
            datefmt=datefmt))
    root.addHandler(logfile_handler)
