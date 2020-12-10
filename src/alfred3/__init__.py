# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>


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
import json
import random
import threading
from builtins import object
from uuid import uuid4
from configparser import NoOptionError
from typing import Union
from pathlib import Path

import pymongo
from cryptography.fernet import Fernet

from . import layout, messages, settings, page
from . import saving_agent
from .section import RootSection
from .alfredlog import QueuedLoggingInterface
from ._helper import _DictObj
from .data_manager import DataManager
from .data_manager import CodeBookExporter
from .data_manager import ExpDataExporter
from .saving_agent import SavingAgentController
from .saving_agent import AutoLocalSavingAgent
from .saving_agent import AutoMongoSavingAgent
from .saving_agent import CodebookLocalSavingAgent
from .saving_agent import CodebookMongoSavingAgent
from .saving_agent import MongoManager
from .ui_controller import WebUserInterfaceController
from .ui_controller import UserInterface
from .ui_controller import MovementManager
from .exceptions import SavingAgentException

_LSA = "local_saving_agent"
_LSA_FB = ["fallback_local_saving_agent", "level2_fallback_local_saving_agent"]
_LSA_U = "local_saving_agent_unlinked"
_LSA_C = "local_saving_agent_codebook"
_F_LSA = "failure_local_saving_agent"
_MSA = "mongo_saving_agent"
_MSA_FB = ["fallback_mongo_saving_agent"]
_MSA_U = "mongo_saving_agent_unlinked"
_MSA_C = "mongo_saving_agent_codebook"


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
        self.root_section = RootSection(self)
        self.movement_manager = MovementManager(self)

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

        if "responsive" in self.config.get("experiment", "web_layout"):
            self._user_interface_controller = UserInterface(self)

        # Allows for session-specific saving of unlinked data.
        self._unlinked_random_name_part = uuid4().hex

        self._data_manager = DataManager(self)
        self._mongo_manager = MongoManager(self)
        self.sac_main = self._init_sac_main()
        self.sac_unlinked = self._init_sac_unlinked()
        self.sac_codebook = self._init_sac_codebook()

        self._saving_agent_controller = self.sac_main

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
        """Checks if a session ID is present. If not, sets it to 'NA'.
        Usually, the session ID is set in localserver.py or alfredo.py.
        This method allows the experiment to be initialized on its own,
        which is very useful for testing. 
        """
        try:
            self.config.get("metadata", "session_id")
        except NoOptionError:
            self.config.read_dict({"metadata": {"session_id": "NA"}})
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
                f"Experiment title: {self.config.get('metadata', 'title')}, "
                f"Experiment version: {self.config.get('metadata', 'version')}"
            )
        )

    def _init_sac_main(self):
        sac_main = SavingAgentController(self)
        init_time = time.strftime("%Y-%m-%d_%H:%M:%S")
        mongodb_filter = {
            "exp_id": self.exp_id,
            "type": DataManager.EXP_DATA,
            "session_id": self.session_id,
        }

        if self.config.getboolean(_LSA, "use"):
            agent_local = AutoLocalSavingAgent(config=self.config[_LSA], experiment=self)
            agent_local.filename = f"{init_time}_{agent_local.name}_{self.session_id}.json"
            for fb in _LSA_FB:
                if self.config.getboolean(fb, "use"):
                    fb_agent = AutoLocalSavingAgent(config=self.config[fb], experiment=self)
                    fb_agent.filename = f"{init_time}_{fb_agent.name}_{self.session_id}.json"
                    agent_local.append_fallback(fb_agent)
            sac_main.append(agent_local)

        if self.config.getboolean(_F_LSA, "use"):
            agent_fail = AutoLocalSavingAgent(config=self.config[_F_LSA], experiment=self)
            agent_fail.filename = f"{init_time}_{agent_fail.name}_{self.session_id}.json"
            sac_main.append_failure_agent(agent_fail)

        if self.secrets.getboolean(_MSA, "use"):
            agent_mongo = self._mongo_manager.init_agent(section=_MSA, fallbacks=_MSA_FB)
            agent_mongo.identifier = mongodb_filter
            for fb_agent in agent_mongo.fallback_agents:
                fb_agent.identifier = mongodb_filter
            sac_main.append(agent_mongo)

        if self.config.getboolean(_MSA, "use"):
            agent_mongo_bw = self._mongo_manager.init_agent(
                section=_MSA, fallbacks=_MSA_FB, config_name="config"
            )
            agent_mongo_bw.identifier = mongodb_filter
            for fb_agent in agent_mongo_bw.fallback_agents:
                fb_agent.identifier = mongodb_filter
            msg = (
                "Initialized a MongoSavingAgent that was configured in config.conf. "
                "This is deprecated. Please configure your MongoSavingAgents in secrets.conf."
            )
            DeprecationWarning(msg)
            self.log.warning(msg)
            sac_main.append(agent_mongo_bw)

        return sac_main

    def _init_sac_unlinked(self):

        sac_unlinked = SavingAgentController(self)

        if self.config.getboolean(_LSA_U, "use"):
            agent_loc_unlnkd = AutoLocalSavingAgent(config=self.config[_LSA_U], experiment=self)
            agent_loc_unlnkd.filename = f"unlinked_{self._unlinked_random_name_part}.json"
            sac_unlinked.append(agent_loc_unlnkd)

        if self.secrets.getboolean(_MSA_U, "use"):
            agent_mongo_unlinked = self._mongo_manager.init_agent(
                section=_MSA_U, fill_section=_MSA
            )
            agent_mongo_unlinked.identifier = {
                "exp_id": self.exp_id,
                "type": DataManager.UNLINKED_DATA,
                "_id": agent_mongo_unlinked.doc_id,
            }
            sac_unlinked.append(agent_mongo_unlinked)

        return sac_unlinked

    def _init_sac_codebook(self):

        sac_codebook = SavingAgentController(self)

        if self.config.getboolean(_LSA_C, "use"):
            agent_local = CodebookLocalSavingAgent(config=self.config[_LSA_C], experiment=self)
            title = self.title.lower().replace(" ", "_")
            agent_local.filename = f"codebook_{title}_v{self.version}.json"
            sac_codebook.append(agent_local)

        if self.secrets.getboolean(_MSA_C, "use"):
            agent_mongo = self._mongo_manager.init_agent(
                agent_class=CodebookMongoSavingAgent, section=_MSA_C, fill_section=_MSA,
            )
            agent_mongo.identifier = {
                "exp_id": self.exp_id,
                "exp_version": self.version,
                "type": DataManager.CODEBOOK_DATA,
            }
            sac_codebook.append(agent_mongo)

        return sac_codebook

    def start(self):
        """
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        """
        self.page_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.log.info("Experiment.start() called. Session is starting.")
        self._user_interface_controller.start()

    def finish(self):
        """
        Beendet das Experiment. Ruft  :meth:`page_controller.PageController.change_to_finished_section` auf und setzt **self._finished** auf *True*.

        """
        if self._finished:
            msg = "Experiment.finish() called. Experiment was already finished. Leave Method"
            self.log.warning(msg)
            
            return
        
        self.log.info("Experiment.finish() called. Session is finishing.")
        
        for page in self.root_section.all_pages:
            if not page.is_closed:
                page.close()
        
        self._finished = True

        if self.config.getboolean("general", "debug"):
            if self.config.getboolean("debug", "disable_saving"):
                
                return
        
        self.save_data()

        if self.config.getboolean("general", "transform_data_to_csv"):
            export_to_csv = threading.Thread(target=self._export_data_to_csv, name="export")
            export_to_csv.start()

    def save_data(self):
        """Saves data with the main, unlinked and codebook :class:`SavingAgentController`s.

        .. warning::
            Note that a call to this function will NOT prompt a call to
            the :meth:`~page.CustomSavingPage.save_data` method of
            :class:`page.CustomSavingPage`s attached to the experiment.
            You need to call those manually.
        """

        data = self.data_manager.get_data()
        self.sac_main.save_with_all_agents(data=data, level=99)

        if self.page_controller.unlinked_data_present():
            for agent in self.sac_unlinked.agents.values():
                unlinked_data = self.data_manager.get_unlinked_data(encrypt=agent.encrypt)
                self.sac_unlinked.save_with_agent(data=unlinked_data, name=agent.name, level=99)

        codebook_data = self.data_manager.get_codebook_data()
        self.sac_codebook.save_with_all_agents(data=codebook_data, level=99)

    def _export_data_to_csv(self):
        csv_directory = Path(self.config.get("general", "csv_directory"))
        if csv_directory.is_absolute():
            data_dir = csv_directory
        else:
            data_dir = Path(self.path) / csv_directory
        data_dir.mkdir(exist_ok=True, parents=True)

        time.sleep(1)

        if self.config.getboolean(_LSA, "use"):
            lsa_name = self.config.get(_LSA, "name")
            lsa_dir = self.sac_main.agents[lsa_name].directory
            exp_exporter = ExpDataExporter()
            exp_exporter.write_local_data_to_file(
                in_dir=lsa_dir, out_dir=data_dir, data_type=DataManager.EXP_DATA, overwrite=True
            )
            self.log.info(f"Exported experiment data to '{str(data_dir)}'")

        any_unlinked_page = any([isinstance(pg, page.UnlinkedDataPage) for pg in self.page_controller.all_pages])
        if self.config.getboolean(_LSA_U, "use") and any_unlinked_page:
            lsa_name = self.config.get(_LSA_U, "name")
            lsa_dir = self.sac_unlinked.agents[lsa_name].directory
            unlinked_exporter = ExpDataExporter()
            unlinked_exporter.write_local_data_to_file(
                in_dir=lsa_dir,
                out_dir=data_dir,
                data_type=DataManager.UNLINKED_DATA,
                overwrite=True,
            )
            self.log.info(f"Exported unlinked data to '{str(data_dir)}'")

        if self.config.getboolean(_LSA_C, "use"):
            lsa_name = self.config.get(_LSA_C, "name")
            cb_name = self.sac_codebook.agents[lsa_name].file
            cb_exporter = CodeBookExporter()
            cb_exporter.write_local_data_to_file(in_file=cb_name, out_dir=data_dir, overwrite=True)
            self.log.info(f"Exported codebook data to '{str(data_dir)}'")

    def get_page_data(self, page_uid):
        return self.data_manager.find_experiment_data_by_uid(uid=page_uid)

    def append(self, *items):
        for item in items:
            self.page_controller.append(item)

    @property
    def final_page(self):
        return self.page_controller.final_page
    
    @final_page.setter
    def final_page(self, value):
        if not isinstance(value, page.PageCore):
            raise ValueError("Not a valid page.")

        self.page_controller.final_page = value

    
    def change_final_page(self, page):
        msg = "'change_final_page' is deprecated. Please use the setter for 'final_page'."
        DeprecationWarning(msg)
        self.log.warning(msg)
        self.page_controller.append_item_to_finish_section(page)

    def subpath(self, path: Union[str, Path]) -> Path:
        """Returns the full path of an experiment subdirectory.
        
        If the given *path* is absolute, it will not be altered (but 
        transformed to a pathlib.Path object).
        """
        if Path(path).is_absolute():
            return Path(path)
        else:
            return Path(self.path) / path

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

    def encrypt(self, data) -> str:
        """Converts input (given in `data` ) to `bytes`, performs 
        encryption, and returns the encrypted object as ` str`.

        In web experiments deployed via mortimer, a safe, user-specific 
        secret key will be used for encryption. The method will also 
        work in offline experiments, but does NOT provide safe 
        encryption in this case, as a PUBLIC key is used for encryption. 
        This is only ok for testing purposes.

        Args:
            data: Input object that you want to encrypt. If the input is
                *None*, the function will return *None*.
        """
        if data is None:
            return None

        if type(data) not in [str, int, float]:
            raise TypeError("Input must be of type str, int, or float.")

        d_str = str(data)
        d_bytes = d_str.encode()

        if self.secrets.getboolean("encryption", "public_key"):
            self.log.warning(
                "USING STANDARD PUBLIC ENCRYPTION KEY. YOUR DATA IS NOT SAFE! USE ONLY FOR TESTING"
            )

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
        return self.root_section

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

        :return: :py:class:`SavingAgentController`
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
