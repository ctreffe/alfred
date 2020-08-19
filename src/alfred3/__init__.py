# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

alfred enthält die Basisklasse :py:class:`Experiment`

"""

from __future__ import absolute_import

from ._version import __version__

# init logger at the top for working inheritance
from . import alfredlog

logger = alfredlog.getLogger(__name__)

import os
import sys
import time
import logging
from builtins import object
from uuid import uuid4
from configparser import NoOptionError

from cryptography.fernet import Fernet

from . import layout, messages, settings
from .alfredlog import QueuedLoggingInterface
from ._helper import _DictObj
from .data_manager import DataManager
from .page_controller import PageController
from .saving_agent import SavingAgentController
from .ui_controller import WebUserInterfaceController


class Experiment(object):
    def __init__(
        self, config: dict = None, config_string=None, basepath=None, custom_layout=None,
    ):

        self._alfred_version = __version__
        self._session_status = None

        self.config = config.get("exp_config")
        self.secrets = config.get("exp_secrets")

        self._init_logging()
        self._set_encryptor()

        # update settings with custom settings from mortimer
        # TODO: Remove self._settings altogether
        self._settings = settings.ExperimentSpecificSettings(config_string)
        self._settings.navigation = _DictObj(self.config["navigation"])
        self._settings.hints = _DictObj(self.config["hints"])
        self._settings.messages = _DictObj(self.config["messages"])

        self._message_manager = messages.MessageManager()
        self._experimenter_message_manager = messages.MessageManager()
        self._page_controller = PageController(self)

        # Determine web layout if necessary
        # TODO: refactor layout and UIController initializiation code
        # pylint: disable=no-member
        self._type = "web"  # provided for backwards compatibility
        if self._type == "web" or self._type == "qt-wk":
            if custom_layout:
                web_layout = custom_layout
            elif "web_layout" in self._settings.experiment and hasattr(
                layout, self._settings.experiment.web_layout
            ):
                web_layout = getattr(layout, self._settings.experiment.web_layout)()
            elif "web_layout" in self._settings.experiment and not hasattr(
                layout, self._settings.experiment.web_layout
            ):
                self.log.warning(
                    "Layout specified in config.conf does not exist! Switching to BaseWebLayout"
                )
                web_layout = None

        if self._type == "web":
            self._user_interface_controller = WebUserInterfaceController(self, layout=web_layout)

        else:
            ValueError("unknown type: '%s'" % self._type)

        self._data_manager = DataManager(self)
        self._saving_agent_controller = SavingAgentController(self)

        self._condition = ""
        self._session = ""
        self._finished = False
        self._start_timestamp = None
        self._start_time = None

        if basepath is not None:
            self.log.warning("Usage of basepath is deprecated.")

        if config_string is not None:
            self.log.warning(
                (
                    "Usage of config_string is deprecated. Use "
                    + "alfred3.config.ExperimentConfig with the appropriate arguments instead."
                )
            )

    def _session_id_check(self):
        """Checks if a session ID is present. If not, sets it to 'n/a'.
        Usually, the session ID is set in localserver.py or alfredo.py.
        This method allows the experiment to be initialized on its own,
        which is very useful for testing. 
        """
        try:
            self.config.get("metadata", "session_id")
        except NoOptionError:
            self.config.read_dict({"metadata": {"session_id": "n/a"}})
            self.log.info(
                (
                    "Session ID could not be accessed. This might be valid for testing."
                    "In production, you should always have a valid session ID."
                )
            )

    def _init_logging(self):
        self.log = QueuedLoggingInterface(base_logger="alfred3", queue_logger="exp." + self.exp_id)
        self._session_id_check()
        self.log.session_id = self.config.get("metadata", "session_id")

        self.log.info(
            (
                f"Alfred {self.config.get('experiment', 'type')} experiment session initialized! "
                f"Alfred version: {self.alfred_version}, "
                f"experiment title: {self.config.get('metadata', 'title')}, "
                f"experiment version: {self.config.get('metadata', 'version')}"
            )
        )

    def start(self):
        """
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        """
        self.page_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime("%Y-%m-%d_t%H%M%S")
        self.log.info("Experiment.start() called. Session is starting.")
        self._user_interface_controller.start()

    def finish(self):
        """
        Beendet das Experiment. Ruft  :meth:`page_controller.PageController.change_to_finished_section` auf und setzt **self._finished** auf *True*.

        """
        if self._finished:
            self.log.warning(
                "Experiment.finish() called. Experiment was already finished. Leave Method"
            )
            return
        self.log.info("Experiment.finish() called. Session is finishing.")
        self._finished = True
        self._page_controller.change_to_finished_section()

        # run saving_agent_controller
        self._saving_agent_controller.run_saving_agents(99)

    def append(self, *items):
        for item in items:
            self.page_controller.append(item)

    def change_final_page(self, page):
        self.page_controller.append_item_to_finish_section(page)

    def subpath(self, path):
        return os.path.join(self.path, path)

    @property
    def alfred_version(self):
        return self._alfred_version

    @property
    def author(self):
        """
        Achtung: *read-only*

        :return: Experiment author **author** (*str*)
        """
        return self.config.get("metadata", "author")

    @property
    def type(self):
        """
        Achtung: *read-only*

        :return: Type of experiment **type** (*str*)
        """

        return self.config.get("experiment", "type")

    @property
    def version(self):
        """
        Achtung: *read-only*

        :return: Experiment version **version** (*str*)
        """
        return self.config.get("metadata", "version")

    @property
    def title(self):
        """
        Achtung: *read-only*

        :return: Experiment title **title** (*str*)
        """
        return self.config.get("metadata", "title")

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def start_time(self):
        return self._start_time

    @property
    def message_manager(self):
        return self._message_manager

    @property
    def experimenter_message_manager(self):
        return self._experimenter_message_manager

    @property
    def exp_id(self):
        return self.config.get("metadata", "exp_id")

    @property
    def path(self):
        return str(self.config.expdir)

    @property
    def session_id(self):
        return self.config.get("metadata", "session_id")

    def _set_encryptor(self):
        """Sets the experiments encryptor.

        Four possible outcomes:

        1. Encryptor with key from default secrets.conf
            If neither environment variable nor non-public custom key 
            in the experiments' *secrets.conf* is defined.
        2. Encryptor with key from environment variable
            If 'ALFRED_ENCRYPTION_KEY' is defined in the environment
            and no non-public custom key is defined in the experiments'
            *secrets.conf*.
        3. Encryptor with key from experiment secrets.conf
            If 'public_key = false' and a key is defined in the 
            experiments' *secrets.conf*.
        4. No encryptor
            If 'public_key = false' and no key is defined in the 
            experiments' *secrets.conf*.

        """

        key = os.environ.get("ALFRED_ENCRYPTION_KEY", None)

        if not key or not self.secrets.getboolean("encryption", "public_key"):
            key = self.secrets.get("encryption", "key")

        if key:
            self._encryptor = Fernet(key=key.encode())
        else:
            self.log.warning(
                "No encryption key found. Thus, no encryptor was set, and the methods 'encrypt' and 'decrypt' will not work."
            )

        if self.secrets.getboolean("encryption", "public_key"):
            self.log.warning(
                "USING STANDARD PUBLIC ENCRYPTION KEY. YOUR DATA IS NOT SAFE! USE ONLY FOR TESTING"
            )

    @property
    def session_status(self):
        return self._session_status

    @session_status.setter
    def session_status(self, status):
        """Sets the session_status for the current experiment.

        Args:
            status (str): A string describing the current status of the
                experiment.
                
        Todo:
            Should updates to an experiment's status result in a saving
            action? We could call the SavingAgentController from within
            this method to save the dataset every time a status update
            is performed.
            ATTENTION: The status is currently not saved in Alfed but
            exists only at runtime!
        """
        if not isinstance(status, str):
            raise TypeError
        self._session_status = status

    def set_additional_data(self, key: str, value):
        """Shortcut for :meth:`DataManager.add_additional_data`.
        """
        self.data_manager.add_additional_data(key, value)

    def get_additional_data(self, key: str):
        """Shortcut for :meth:`DataManager.get_additional_data_by_key`.
        """
        return self.data_manager.get_additional_data_by_key(key)

    def get_page_data(self, uid):
        """Shortcut for :meth:`DataManager.find_experiment_data_by_uid`.
        """
        return self.data_manager.find_experiment_data_by_uid(uid)

    def encrypt(self, data) -> str:
        """Converts input (given in `data` ) to `bytes`, performs encryption, and returns the encrypted object as ` str`.

        In web experiments deployed via mortimer, a safe, user-specific secret key will be used for encryption. The method will also work in offline experiments, but does NOT provide safe encryption in this case, as a PUBLIC key is used for encryption. This is only ok for testing purposes.

        :param data: Input object that you want to encrypt.
        """
        if type(data) not in [str, int, float]:
            raise TypeError("Input must be of type str, int, or float.")

        d_str = str(data)

        d_bytes = d_str.encode()
        encrypted = self._encryptor.encrypt(d_bytes)
        return encrypted.decode()

    def decrypt(self, data):
        """Decrypts input and returns the decrypted object as `str`.

        The method uses the built-in Fernet instance to decrypt the input.

        :param data: Encrypted bytes object. Must be of type `str` or `bytes`.
        """
        if type(data) is str:
            d_bytes = data.encode()
        elif type(data) is bytes:
            d_bytes = data
        else:
            raise TypeError("Input must be of type str or bytes.")

        d = self._encryptor.decrypt(d_bytes)
        return d.decode()

    @property
    def user_interface_controller(self):
        """
        Achtung: *read-only*

        :return: :py:class:`ui_controller.QtUserInterfaceController` oder :py:class:`ui_controller.WebUserInterfaceController`
        """
        return self._user_interface_controller

    @property
    def page_controller(self):
        """
        Achtung: *read-only*

        :return: :py:class:`page_controller.PageController`
        """
        return self._page_controller

    @property
    def data_manager(self):
        """
        Achtung: *read-only*

        :return: :py:class:`data_manager.DataManager`
        """
        return self._data_manager

    @property
    def saving_agent_controller(self):
        """
        Achtung: *read-only*

        :return: :py:class:`saving_agent.SavingAgentController`
        """
        return self._saving_agent_controller

    @property
    def settings(self):
        return self._settings

    @property
    def finished(self):
        """
        Achtung: *read-only*

        :return: Experiment beendet? **self._finished** (*bool*)
        """
        return self._finished

    @property
    def condition(self):
        """
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        """
        return self._condition

    def add_condition(self, s):
        self._condition = self._condition + "." + s if self._condition else s

    @property
    def session(self):
        """
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        """
        return self._session

    def add_session(self, s):
        self._session = self._session + "." + s if self._session else s

    def __iadd__(self, other):
        self.append(other)
        return self
