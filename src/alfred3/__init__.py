# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

alfred enthält die Basisklasse :py:class:`Experiment`

"""

from __future__ import absolute_import

from ._version import __version__

import os
import sys
import time
import logging
from builtins import object
from uuid import uuid4

from cryptography.fernet import Fernet

from . import alfredlog, layout, messages, settings
from ._helper import _DictObj
from .data_manager import DataManager
from .page_controller import PageController
from .saving_agent import SavingAgentController
from .ui_controller import WebUserInterfaceController

logger = logging.getLogger(__name__)


class Experiment(object):
    def __init__(
        self,
        config: dict = None,
        config_string="",
        basepath=None,
        custom_layout=None,
    ):

        self._alfred_version = __version__
        self.config = config.get("exp_config")
        self.secrets = config.get("exp_secrets")


        # Experiment startup message
        logger.info(
            (
                f"Alfred {self.config.get('experiment', 'type')} experiment session initialized! "
                f"Alfred version: {self._alfred_version}, "
                f"experiment title: {self.config.get('metadata', 'title')}, "
                f"experiment version: {self.config.get('metadata', 'version')}"
            )
        )

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
                logger.warning(
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
            logger.warning("Usage of basepath is deprecated.")

        if config_string is not None:
            logger.warning(
                (
                    "Usage of config_string is deprecated. Use "
                    + "alfred3.config.ExperimentConfig with the appropriate arguments instead."
                )
            )

        # # Set encryption key
        # if config and config["encryption_key"]:
        #     self._encryptor = Fernet(config["encryption_key"])
        #     logger.info("Using mortimer-generated encryption key.", self)
        # else:
        #     self._encryptor = Fernet(b"OnLhaIRmTULrMCkimb0CrBASBc293EYCfdNuUvIohV8=")
        #     logger.warning("Using PUBLIC encryption key. USE ONLY FOR TESTING.", self)

    # TODO: Delete deprecated method
    # def update(self, title, version, author, exp_id, type="web"):
    #     self._title = title
    #     self._version = version
    #     self._author = author
    #     self._type = type
    #     self._exp_id = exp_id

    def start(self):
        """
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        """
        self.page_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime("%Y-%m-%d_t%H%M%S")
        logger.info("Experiment.start() called. Session is starting.")
        self._user_interface_controller.start()

    def finish(self):
        """
        Beendet das Experiment. Ruft  :meth:`page_controller.PageController.change_to_finished_section` auf und setzt **self._finished** auf *True*.

        """
        if self._finished:
            logger.warning(
                "Experiment.finish() called. Experiment was already finished. Leave Method"
            )
            return
        logger.info("Experiment.finish() called. Session is finishing.")
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

    # TODO: Deal with encryptor
    # def encrypt(self, data) -> str:
    #     """Converts input (given in `data` ) to `bytes`, performs encryption, and returns the encrypted object as ` str`.

    #     In web experiments deployed via mortimer, a safe, user-specific secret key will be used for encryption. The method will also work in offline experiments, but does NOT provide safe encryption in this case, as a PUBLIC key is used for encryption. This is only ok for testing purposes.

    #     :param data: Input object that you want to encrypt.
    #     """
    #     if type(data) not in [str, int, float]:
    #         raise TypeError("Input must be of type str, int, or float.")

    #     d_str = str(data)

    #     d_bytes = d_str.encode()
    #     encrypted = self._encryptor.encrypt(d_bytes)
    #     return encrypted.decode()

    # def decrypt(self, data):
    #     """Decrypts input and returns the decrypted object as `str`.

    #     The method uses the built-in Fernet instance to decrypt the input.

    #     :param data: Encrypted bytes object. Must be of type `str` or `bytes`.
    #     """
    #     if type(data) is str:
    #         d_bytes = data.encode()
    #     elif type(data) is bytes:
    #         d_bytes = data
    #     else:
    #         raise TypeError("Input must be of type str or bytes.")

    #     d = self._encryptor.decrypt(d_bytes)
    #     return d.decode()

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
