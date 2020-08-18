# -*- coding: utf-8 -*-
"""Run an alfred experiment.

You can either use the command line interface via 
``python3 -m alfred3.run`` from within your experiment directory, or 
import the `run_experiment` function into your own `run.py` and run it 
from there.

Example for importing and running the `run_experiment` function:

.. code-block:: python

    from alfred3.run import ExperimentRunner

    if __name__ == "__main__":
        runner = ExperimentRunner()
        runner.auto_run()

If you want more control over how the app is being run, you can call
the individual methods by hand and call :meth:`ExperimentRunner.app.run`
with arguments of your choice.

.. code-block:: python
    from alfred3.run import ExperimentRunner

    if __name__ == "__main__":
        runner = ExperimentRunner()
        runner.generate_session_id()
        runner.configure_logging()
        runner.create_experiment_app()
        runner.set_port()
        runner.start_browser_thread()
        runner.print_startup_message()
        runner.app.run(use_reloader=False, debug=False)

"""

import importlib
import sys
import webbrowser
import os
import threading
import logging
from pathlib import Path
from uuid import uuid4

import click
from flask import Flask
from thesmuggler import smuggle

from alfred3.helpmates import socket_checker, ChromeKiosk, localserver
from alfred3 import alfredlog
from alfred3 import settings
from alfred3.config import init_configuration


class ExperimentRunner:
    def __init__(self, path: str = None):
        self.expdir = Path(path).resolve() if path else Path.cwd()
        self.config = init_configuration(self.expdir)
        self.app = None
        self.expurl = None

    def generate_session_id(self):
        session_id = uuid4().hex
        self.config["exp_config"].read_dict({"metadata": {"session_id": session_id}})

    def configure_logging(self):
        """Sets some sensible logging configuration for local 
        experiments.

        * Base logger gets turned off to avoid doubled logging messages
            (we don't want to turn the queue_logger off, because that
            way usage is completely the same between local and web exp.)
        
        * Queue logger gets configured using settings from config.conf
        """
        config = self.config["exp_config"]

        exp_id = config.get("metadata", "exp_id")
        loggername = f"exp.{exp_id}"
        logger = logging.getLogger(loggername)

        formatter = alfredlog.prepare_alfred_formatter(exp_id)

        if config.getboolean("general", "debug"):
            logfile = "alfred_debug.log"
        else:
            logfile = "alfred.log"

        logpath = Path(config.get("log", "path")).resolve() / logfile
        if not logpath.is_absolute():
            logpath = self.expdir / logpath
        file_handler = alfredlog.prepare_file_handler(logpath)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        logger.setLevel(alfredlog.parse_level(config.get("log", "level")))

        base_logger = logging.getLogger("alfred3")
        base_logger.addHandler(logging.NullHandler())

    def create_experiment_app(self):
        script = smuggle(str(self.expdir / "script.py"))
        # set generate_experiment function
        localserver.Script.expdir = self.expdir
        localserver.Script.config = self.config
        localserver.Script.generate_experiment = script.generate_experiment
        self.app = localserver.app
        self.app.secret_key = self.config["exp_secrets"].get("flask", "secret_key")

        return self.app

    def set_port(self):
        port = 5000
        while not socket_checker(port):
            port += 1
        self.port = port

    def print_startup_message(self):

        sys.stderr.writelines(
            [f" * Start local experiment using http://127.0.0.1:{self.port}/start\n"]
        )

    def _open_browser(self):

        # generate url
        expurl = "http://127.0.0.1:{port}/start".format(port=self.port)

        if self.config["exp_config"].getboolean("experiment", "fullscreen"):
            ChromeKiosk.open(url=expurl)
        else:
            webbrowser.open(url=expurl)

    def start_browser_thread(self):
        # start browser in a thread (needed for windows)
        browser = threading.Thread(target=self._open_browser)
        browser.start()

    def auto_run(self, open_browser: bool = True, debug=False):
        self.generate_session_id()
        self.configure_logging()
        self.create_experiment_app()
        self.set_port()
        if open_browser:
            self.start_browser_thread()
        self.print_startup_message()
        self.app.run(port=self.port, threaded=True, use_reloader=False, debug=debug)


@click.command()
@click.option(
    "-a/-m",
    "--auto-open/--manual-open",
    default=True,
    help="If this flag is set to '-a', the experiment will open a browser window automatically. [default: '-a']",
)
@click.option("--path", default=Path.cwd())
@click.option(
    "-debug/-production",
    "--debug/--production",
    default=False,
    help="If this flag is set to to '-debug', the alfred experiment will start in flask's debug mode. [default: '-production']",
)
def run_cli(path, auto_open, debug):
    runner = ExperimentRunner(path)
    runner.auto_run(open_browser=auto_open, debug=debug)


if __name__ == "__main__":
    run_cli()  # pylint: disable=no-value-for-parameter
