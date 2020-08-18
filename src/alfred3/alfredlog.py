"""Provides basic logging configuration for alfred experiments.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from builtins import object
import logging
import sys
import os
import traceback
import queue
import threading
import copy
import re
from pathlib import Path
from typing import Union

from .config import ExperimentConfig


def init_logging(name: str):
    """Initialize logging with configuration from config.conf.

    Included for backwards compatibility with old run.py from v1.2.0
    onwards.

    TODO: Remove in v2.0.0
    """

    wd = Path.cwd()
    config = ExperimentConfig(wd)

    formatter = prepare_alfred_formatter(exp_id=config.get("metadata", "exp_id"))

    logdir = Path(config.get("log", "path")).resolve()
    logfile = logdir / "alfred.log"
    file_handler = prepare_file_handler(filepath=logfile)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    alfred_logger = logging.getLogger("alfred")
    alfred3_logger = logging.getLogger("alfred3")

    level = config.get("log", "level").upper()

    alfred_logger.addHandler(file_handler)
    alfred_logger.addHandler(stream_handler)
    alfred_logger.setLevel(getattr(logging, level))
    alfred3_logger.addHandler(file_handler)
    alfred3_logger.addHandler(stream_handler)
    alfred3_logger.setLevel(getattr(logging, level))

    msg = (
        "The function init_logging is deprecated. You are probably seeing this warning, "
        "because you are using the traditional run.py formulation. "
        "Please switch to the current version. "
        "The function will be removed in the next major release."
    )

    DeprecationWarning(msg)

    if name == "alfred":
        alfred_logger.warning(msg)
    elif name == "alfred3":
        alfred3_logger.warning(msg)
    else:
        logger = logging.getLogger(name)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(getattr(logging, level))
        logger.warning(msg)


def getLogger(name: str):
    """Get an instance of :class:`QueuedLoggingInterface` with a
    *queue_logger* of the given name.

    Included for backwards compatibility from v1.2.0 onwards.

    TODO: Remove in v2.0.0
    """

    return QueuedLoggingInterface(queue_logger=name)


def prepare_file_handler(filepath: Union[str, Path]) -> logging.FileHandler:
    """Returns a :class:`~logging.FileHandler` and creates the necessary
    directories on the fly, if needed.

    Args:
        filepath: Absolute path to the targeted logfile.
    """
    logpath = Path(filepath)

    if not logpath.is_absolute():
        raise ValueError("Value of filepath must be an absolute path.")

    if logpath.is_dir():
        raise ValueError("Value of filepath must point to a file.")

    logdir = logpath.parent
    logdir.mkdir(exist_ok=True)

    return logging.FileHandler(str(logpath))


def prepare_alfred_formatter(exp_id: str) -> logging.Formatter:
    """Returns a :class:`~logging.Formatter` with the standard alfred
    logging format, including experiment id.
    """

    formatter = logging.Formatter(
        ("%(asctime)s - %(name)s - %(levelname)s - " f"experiment id={exp_id} - %(message)s")
    )

    return formatter


def parse_level(level: str) -> int:
    """Parses level definitions in lower case strings and returns the
    approriate level attribute of the Python logging library.
    """
    lvl = level.upper()
    if lvl not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("log level must be debug, info, warning, error or critical")
    return getattr(logging, lvl)


class QueuedLoggingInterface:
    """Interface for handling logging in alfred3.

    This class provides access to two loggers: The base logger and
    the queue logger. The reasoning is the following:

    * We want logging messages to contain experiment information
        (exp_id and session_id) and we want logfiles to potentially be
        experiment specific.
    
    * The necessary information only becomes available to pages and elements
        once the page or its parent section get appended to the 
        experiment.
    
    * So, logged messages are collected in a queue and logged as soon 
        as the experiment becomes available.
    
    * In order to not lose information in between their queueing
        and their eventual logging with the queue logger, all messages
        get also logged immediately using the base logger to a general
        "admin" log (this is turned off through configuration
        in run.py for local experiments by default, to avoid doubling
        log messages in a single file).
    
    Args:
        base_logger: Name of the base logger.
        queue_logger: Name of the queue logger.

    Attributes:
        use_base_logger (bool): Indicates, whether the base logger 
            should be used. Defaults to *True*, if a *base_logger* is
            defined upon initialization and to *False*, if *base_logger*
            is *None*. You can use this to turn off base logger usage.
        
        queue_logger (logging.Logger): The queue logger object. You
            can acces the logger this way to apply advanced 
            configuration.
        
        session_id (str): Allows you to set a session ID that will be
            included in logged messages. (Defaults to "n/a".)
    """

    def __init__(self, base_logger: str = None, queue_logger: str = None):
        """Constructor method."""
        self.use_base_logger = True if base_logger is not None else False
        self._base_logger = logging.getLogger(base_logger) if base_logger is not None else None
        self._base_logger_storage = None
        self._queue_logger = logging.getLogger(queue_logger) if queue_logger is not None else None
        self._queue = queue.Queue()
        self._level = None
        self.session_id = "n/a"

    @property
    def queue_logger(self):
        return self._queue_logger

    @queue_logger.setter
    def queue_logger(self, logger):
        if not self.queue_logger:
            self._queue_logger = logger
        else:
            raise ValueError("Queue logger is already set and can only be set once.")

    def _unpack_worker(self):
        while not self._queue.empty():
            level, msg = self._queue.get()
            lvl_logger = getattr(self.queue_logger, level)
            lvl_logger(msg)

    def log_queued_messages(self):
        """Logs messages in the queue using the queue logger."""
        if self.queue_logger is None:
            pass

        if self._level:
            self.queue_logger.setLevel(self._level)
        threading.Thread(target=self._unpack_worker).start()

    def setLevel(self, level: str):
        """Sets a level for the queue logger. Since the level will be
        stored, this can be done even before a queue logger is defined.
        """

        if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                "Level must be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'."
            )

        self._level = getattr(logging, level.upper())

        if self.queue_logger:
            self.queue_logger.setLevel(self._level)

    def _handle_msg(self, msg: str, level: str, *args, **kwargs):

        msg = f"session id={self.session_id} - " + msg

        if self.use_base_logger:
            getattr(self._base_logger, level)(msg, *args, **kwargs)

        if not self.queue_logger:
            self._queue.put((level, msg))
        else:
            logger_lvl = getattr(self.queue_logger, level)
            try:
                logger_lvl(msg, *args, **kwargs)
            except TypeError:
                logger_lvl(*args, **kwargs)

    def deactivate_base_logger(self):
        self._base_logger_storage = self._base_logger
        self._base_logger = None
        self.use_base_logger = False

    def activate_base_logger(self):
        if not self._base_logger:
            self._base_logger = self._base_logger_storage
        self.use_base_logger = True

    def log(self, level: str, msg: str, *args, **kwargs):
        """Log a message with a level handed over in the *level*
        argument."""
        self._handle_msg(msg, level, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log a message with level 'debug'."""
        self._handle_msg(msg, "debug", *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log a message with level 'info'."""
        self._handle_msg(msg, "info", *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a message with level 'warning'."""
        self._handle_msg(msg, "warning", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log a message with level 'error'."""
        self._handle_msg(msg, "error", *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log a message with level 'critical'."""
        self._handle_msg(msg, "critical", *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log a message with level 'exception'."""
        self._handle_msg(msg, "exception", *args, **kwargs)
