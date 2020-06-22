"""Provides basic logging configuration for alfred experiments.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from builtins import object
import logging
import sys
import os
import traceback
from pathlib import Path

from .config import ExperimentConfig


def init_logging(name: str, config: ExperimentConfig):
    """Initializes logging for an experiment.

    This is meant to be called only once, usually in *run.py*.It sets a 
    formatter, a file handler, and a stream handler. The directory in 
    which the logfile is placed and the log level are determined based
    on *config*. A logging message will have the following format::

        2020-06-12 17:51:56,155 - name - INFO - experiment id=1234, session id=1234 - msg

    Args:
        name: Name of the root logger.
        config: An experiment configuration instance. For initialization,
            it only needs to have a "log" section.
    """
    exp_id = config.get("metadata", "exp_id")
    session_id = config.get("metadata", "session_id")
    logger = logging.getLogger(name)

    formatter = logging.Formatter(
        (
            "%(asctime)s - %(name)s - %(levelname)s - "
            f"experiment id={exp_id}, session id={session_id} - %(message)s"
        )
    )

    # create file handler
    logpath = Path(config.get("log", "path"))
    if not logpath.is_absolute():
        logpath = config.expdir / logpath
    logpath.mkdir(exist_ok=True)
    if not config.getboolean("general", "debug"):
        logfile = logpath / "alfred.log"
    else:
        logfile = logpath / "alfred_debug.log"
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)

    # create stream handler
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    # get level
    lvl = config.get("log", "level").upper()
    if lvl not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("log level must be debug, info, warning, error or critical")

    # apply configuration
    logger.setLevel(getattr(logging, lvl))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
