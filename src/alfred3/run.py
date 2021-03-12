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

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>
"""

import importlib
import sys
import webbrowser
import os
import threading
import logging
import platform
import subprocess
from pathlib import Path
from uuid import uuid4

import click
from thesmuggler import smuggle

from alfred3._helper import socket_checker
from alfred3 import localserver
from alfred3 import alfredlog
from alfred3.config import ExperimentConfig
from alfred3.config import ExperimentSecrets

class ExperimentRunner:
    def __init__(self, path: str = None):
        self.expdir = self.find_path(path)
        self.config = ExperimentConfig(self.expdir)
        self.secrets = ExperimentSecrets(self.expdir)
        self.app = None
        self.expurl = None

    def find_path(self, path):
        if path:
            p = Path(path).resolve()
            script0 = p / "script.py"
            if script0.is_file():
                sys.stderr.writelines([f" * Using script '{str(script0)}'\n"])
                return p

        fp = Path(sys.argv[0]).resolve().parent
        script2 = fp / "script.py"
        if script2.is_file():
            sys.stderr.writelines([f" * Using script '{str(script2)}'\n"])
            return fp

        wd = Path.cwd()
        script1 = wd / "script.py"
        if script1.is_file():
            sys.stderr.writelines([f" * Using script '{str(script1)}'\n"])
            return wd

        raise FileNotFoundError("No script.py found.")

    def generate_session_id(self):
        session_id = uuid4().hex
        self.config.read_dict({"metadata": {"session_id": session_id}})

    def configure_logging(self):
        """Sets some sensible logging configuration for local 
        experiments.

        * Base logger gets turned off to avoid doubled logging messages
            (we don't want to turn the queue_logger off, because that
            way usage is completely the same between local and web exp.)
        
        * Queue logger gets configured using settings from config.conf
        """
        config = self.config

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

        lvl = config.get("log", "level")
        if config.getboolean("general", "debug"):
            if config.getboolean("debug", "log_level_override"):
                lvl = config.get("debug", "log_level")

        logger.setLevel(alfredlog.parse_level(lvl))

        base_logger = logging.getLogger("alfred3")
        base_logger.addHandler(logging.NullHandler())

    def create_experiment_app(self):
        script = smuggle(str(self.expdir / "script.py"))
        
        localserver.Script.expdir = self.expdir
        localserver.Script.config = self.config
        localserver.Script.secrets = self.secrets
        localserver.Script.exp = script.exp
        
        self.app = localserver.app
        secret_key = self.secrets.get("flask", "secret_key", fallback=None)
        if not secret_key:
            import secrets
            secret_key = secrets.token_urlsafe(16)
        self.app.secret_key = secret_key

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

        if self.config.getboolean("general", "fullscreen"):
            ChromeKiosk.open(url=expurl)
        else:
            webbrowser.open(url=expurl)

    def start_browser_thread(self):
        # start browser in a thread (needed for windows)
        browser = threading.Thread(target=self._open_browser, name="browser")
        browser.start()

    def auto_run(self, open_browser: bool = None, debug=False):
        """
        Automatically runs an alfred experiment.

        Args:
            open_browser: Indicates, whether alfred should try to open
                a new browser window automatically.
            debug: Indicates, whether the underlying flask app should be
                run in debug mode. Defaults to None, which leads to
                taking the value from option 'open_browser' in section
                'general' of config.conf.

        """

        self.generate_session_id()
        self.configure_logging()
        self.create_experiment_app()
        self.set_port()

        open_browser = self.config.getboolean("general", "open_browser") if open_browser is None else open_browser
        if open_browser:
            self.start_browser_thread()
        self.print_startup_message()
        self.app.run(port=self.port, threaded=False, use_reloader=False, debug=debug)


class ChromeKiosk:
    """Open a Chrome window in kiosk mode.
    """

    @classmethod
    def open(cls, url: str, path: str = None):
        """Check operating system and call approriate opening method for opening url in Chrome in kiosk mode.

        This will only work, if Chrome is not currently running.

        Args:
            url: URL to open. Needs to start with "http://" or "https://"
            path: Custom path to chrome.exe on Windows. If none is provided, the default paths for Windows 7 and 10 will be tried.
        """
        current_os = platform.system()

        if not url.startswith("http"):
            raise ValueError("Parameter 'url' needs to start with 'http://' or 'https://'.")

        if current_os == "Windows":
            cls.open_windows(url=url, path=path)
        elif current_os == "Darwin":
            cls.open_mac(url=url)
        elif current_os == "Linux":
            raise NotImplementedError(
                "This method has not been implemented for Linux distributions."
            )

    @staticmethod
    def open_windows(url: str, path: str = None):
        """Open url in Chrome in kiosk mode on Windows."""

        paths = []
        paths.append(Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"))
        paths.append(Path.home().joinpath("AppData/Local/Google/Chrome/Application/chrome.exe"))
        paths.append(Path("C:/Program Files (x86)/Google/Application/chrome.exe"))

        existing_paths = [p for p in paths if p is not None and p.exists()]

        chrome = None

        if path:
            chrome = Path(path)
        else:
            chrome = existing_paths[0]

        if not chrome.exists():
            raise FileNotFoundError(f"Did not find a chrome.exe at {str(chrome)}.")

        subprocess.run([chrome, url, "--kiosk"])

    @staticmethod
    def open_mac(url: str):
        """Open url in Chrome in kisok mode on MacOS."""

        subprocess.run(["open", "-a", "Google Chrome", url, "--args", "--kiosk"])

