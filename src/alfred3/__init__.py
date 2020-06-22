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
from builtins import object
from uuid import uuid4

from cryptography.fernet import Fernet

from . import alfredlog, layout, messages, settings
from ._helper import _DictObj
from .data_manager import DataManager
from .page_controller import PageController
from .saving_agent import SavingAgentController
from .ui_controller import QtWebKitUserInterfaceController, WebUserInterfaceController

logger = alfredlog.getLogger(__name__)


class Experiment(object):
    """
    **Experiment** ist die Basisklasse und somit der allgemeine Objekttyp für alle mit alfred erstellten Experimente.

    |
    """

    def __init__(self, config=None, config_string="", basepath=None, custom_layout=None):
        """
        :param layout custom_layout: Optional parameter for starting the experiment with a custom layout.

        |

        Beschreibung:
            | Bei Aufruf von *Experiment* werden :py:class:`page_controller.PageController`, :py:class:`data_manager.DataManager`
            | und :py:class:`saving_agent.SavingAgentController` initialisiert. Zusätzlich wird ein UserInterfaceController aus
            | :py:mod:`.ui_controller` aufgerufen. Welcher Controller aufgerufen wird, hängt vom deklarierten Expermiment-Typ ab.

        |


        **Momentan implementierte Typen für Experimente:**

        =========  =========================================== ===================================================
        Typ        Beschreibung                                ui_controller
        =========  =========================================== ===================================================
        **'qt'**   Lokales qt-Interface wird genutzt.          :py:class:`ui_controller.QtUserInterfaceController`
        **'web'**  Bereitstellung als HTML-Seite via Webserver :py:class:`ui_controller.WebUserInterfaceController`
        =========  =========================================== ===================================================

        |

        :raises ValueError: Falls Parameter falsch oder nicht übergeben werden.

        |
        |
        """
        self._alfred_version = __version__
        self._session_status = None

        # Set experiment metadata
        if config is not None and "experiment" in config.keys():
            self._author = config["experiment"]["author"]
            self._title = config["experiment"]["title"]
            self._version = config["experiment"]["version"]
            self._exp_id = config["experiment"]["exp_id"]
            self._session_id = config["mortimer_specific"]["session_id"]
            self._type = config["experiment"]["type"]
            self._path = config["mortimer_specific"]["path"]
        else:
            self._author = settings.metadata.author
            self._title = settings.metadata.title
            self._version = settings.metadata.version
            self._exp_id = settings.metadata.exp_id
            self._type = settings.experiment.type
            self._path = settings.general.external_files_dir
            self._session_id = uuid4().hex
            self._type = settings.experiment.type
            self._path = os.path.abspath(os.path.dirname(sys.argv[0]))
        if not self._exp_id:
            raise ValueError("You need to specify an experiment ID.")

        if config is not None:
            self.__db_cred = config.get("db_cred", None)
        else:
            self.__db_cred = None

        # Set encryption key
        if config and config["encryption_key"]:
            self._encryptor = Fernet(config["encryption_key"])
            logger.info("Using mortimer-generated encryption key.", self)
        else:
            self._encryptor = Fernet(b"OnLhaIRmTULrMCkimb0CrBASBc293EYCfdNuUvIohV8=")
            logger.warning("Using PUBLIC encryption key. USE ONLY FOR TESTING.", self)

        # Experiment startup message
        logger.info(
            "Alfred %s experiment session initialized! Alfred version: %s, experiment name: %s, experiment version: %s"
            % (self._type, __version__, self._title, self._version),
            self,
        )

        self._settings = settings.ExperimentSpecificSettings(config_string)
        # update settings with custom settings from mortimer
        if config is not None and "navigation" in config.keys():
            self._settings.navigation = _DictObj(config["navigation"])
        if config is not None and "hints" in config.keys():
            self._settings.hints = _DictObj(config["hints"])
        if config is not None and "messages" in config.keys():
            self._settings.messages = _DictObj(config["messages"])

        self._message_manager = messages.MessageManager()
        self._experimenter_message_manager = messages.MessageManager()
        self._page_controller = PageController(self)

        # Determine web layout if necessary
        # pylint: disable=no-member
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
                    "Layout specified in config.conf does not exist! Switching to BaseWebLayout",
                    self,
                )
                web_layout = None

        if self._type == "web":
            self._user_interface_controller = WebUserInterfaceController(self, layout=web_layout)

        elif self._type == "qt-wk":
            logger.warning("Experiment type qt-wk is experimental!!!", self)
            self._user_interface_controller = QtWebKitUserInterfaceController(
                self, full_scren=settings.experiment.qt_full_screen, weblayout=web_layout,
            )

        else:
            ValueError("unknown type: '%s'" % self._type)

        self._data_manager = DataManager(self)
        self._saving_agent_controller = SavingAgentController(self, db_cred=self.__db_cred)

        self._condition = ""
        self._session = ""
        self._finished = False
        self._start_timestamp = None
        self._start_time = None

        if basepath is not None:
            logger.warning("Usage of basepath is deprecated.", self)

    def update(self, title, version, author, exp_id, type="web"):
        self._title = title
        self._version = version
        self._author = author
        self._type = type
        self._exp_id = exp_id

    def start(self):
        """
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        """
        self.page_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime("%Y-%m-%d_t%H%M%S")
        logger.info("Experiment.start() called. Session is starting.", self)
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
        logger.info("Experiment.finish() called. Session is finishing.", self)
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
        return self._author

    @property
    def type(self):
        """
        Achtung: *read-only*

        :return: Type of experiment **type** (*str*)
        """

        return self._type

    @property
    def version(self):
        """
        Achtung: *read-only*

        :return: Experiment version **version** (*str*)
        """
        return self._version

    @property
    def title(self):
        """
        Achtung: *read-only*

        :return: Experiment title **title** (*str*)
        """
        return self._title

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
        return self._exp_id

    @property
    def path(self):
        return self._path

    @property
    def session_id(self):
        return self._session_id

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
