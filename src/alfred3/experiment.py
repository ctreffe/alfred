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
import functools
import copy
from inspect import isclass
from builtins import object
from uuid import uuid4
from configparser import NoOptionError
from typing import Union
from typing import Dict
from typing import Tuple
from typing import List
from pathlib import Path

import pymongo
from cryptography.fernet import Fernet
from deprecation import deprecated

from .section import Section, RootSection
from .page import Page
from . import messages, page, section
from . import saving_agent
from .alfredlog import QueuedLoggingInterface
from ._helper import _DictObj
from .data_manager import DataManager
from .data_manager import CodeBookExporter
from .data_manager import ExpDataExporter
from .saving_agent import DataSaver
from .ui_controller import UserInterface
from .ui_controller import MovementManager
from .exceptions import SavingAgentException

class Experiment:

    members: Dict[str, Tuple] = {}
    _final_page = None
    _funcs_session_start: List[callable] = []

    condition: str = None
    additional_data: dict = {}
    plugins = {}

    def on_session_start(self, func):
        """Decorator for functions that work on the experiment session.
        
        The decorated function can have an arbitrary name. It *must*
        take an :class:`.ExperimentSession` object as its only argument.

        The purpose of this decorator is to allow manipulation of the
        :class:`.ExperimentSession` object generated by 
        :class:`.Experiment`.

        Example::

            from alfred3 import Experiment

            exp = Experiment()

            @exp.on_session_start
            def prepare(exp):
                exp.condition = "a"

        """

        @functools.wraps(func)
        def wrapper():
            self._funcs_session_start.append(func)
            return func

        return wrapper()

    def member(self, _member=None, *, of_section: str = "_content"):
        """Decorator for adding pages and sections to the experiment.

        Works both with and without arguments.

        Args:
            of_section: Name of the section to which the new member
                shall belong.

        Example::

            from alfred3 import Experiment, page

            exp = Experiment()

            @exp.member
            class HelloWorld(page.Page): pass

        """

        def add_member(member):
            @functools.wraps(member)
            def wrapper():
                self.append(member, to_section=of_section)
                return member

            return wrapper()

        if _member is None:
            return add_member
        else:
            return add_member(_member)
    
    def final_page(self, page):
        """Decorator for adding a custom final page to the experiment.
        
        Example::

            from alfred3 import Experiment, page

            exp = Experiment()

            @exp.final_page
            class Final(page.Page): pass
        
        """
        
        @functools.wraps(page)
        def wrapper():
            self._final_page = page
            return page

        return wrapper()

    def init_members(self) -> dict:
        """Initialize all pages and sections.

        Also appends all members to their parents.

        Returns:
            dict: Dictionary of initialized sections and pages.

        """

        members = {}

        for member_name, (parent_name, member) in self.members.items():
            member_inst = member() if isclass(member) else copy.copy(member)
            members[member_name] = (parent_name, member_inst)

        for parent_name, member_inst in members.values():
            if parent_name == "_content":
                continue
            _, parent = members[parent_name]
            parent += member_inst

        return members

    def start_session(self, config: dict, session_id: str):

        exp_session = ExperimentSession(session_id=session_id, config=config)
        exp_session.additional_data = self.additional_data
        exp_session.plugins = self.plugins

        for func in self._funcs_session_start:
            func(exp_session)

        for parent_name, member in self.init_members().values():
            if parent_name == "_content":
                exp_session += member
        
        if self._final_page is not None:
            exp_session.final_page = self._final_page()
        
        return exp_session

    def append(self, *members, to_section: str = "_content"):
        for member in members:
            if isclass(member):
                name = member.__name__ if member.name is None else member.name
            else:
                name = member.uid if member.name is None else member.name

            if name in self.members or name == "_cotent":
                raise ValueError(f"A section or page of name '{name}' already exists.")

            self.members[name] = (to_section, member)

    def __iadd__(self, other: Union[Section, Page]):
        self.append(other, to_section="_content")
        return self

    def __getattr__(self, name):
        _, member = self.members[name]
        return member

class ExperimentSession:
    def __init__(self, session_id: str, config: dict, **kwargs):
        self.config = config["exp_config"]
        self.secrets = config["exp_secrets"]

        self.log = QueuedLoggingInterface(base_logger="alfred3")
        self.log.queue_logger = logging.getLogger("exp." + self.exp_id)

        self.alfred_version = __version__
        self.session_id = session_id
        self._session_status = None

        self._encryptor = self._set_encryptor()

        self.message_manager = messages.MessageManager()
        self.experimenter_message_manager = messages.MessageManager()
        self.root_section = RootSection(self)
        self.root_section.append_root_sections()
        self.page_controller = self.root_section
        self.movement_manager = MovementManager(self)

        # Determine web layout if necessary
        # TODO: refactor layout and UIController initializiation code
        # pylint: disable=no-member
        self._type = "web"  # provided for backwards compatibility
        # if self._type == "web" or self._type == "qt-wk":
        #     if kwargs.get("custom_layout"):
        #         web_layout = kwargs.get("custom_layout")
        #     elif "web_layout" in settings.experiment and hasattr(
        #         layout, settings.experiment.web_layout
        #     ):
        #         web_layout = getattr(layout, settings.experiment.web_layout)()
        #     elif "web_layout" in settings.experiment and not hasattr(
        #         layout, settings.experiment.web_layout
        #     ):
        #         self.log.warning(
        #             "Layout specified in config.conf does not exist! Switching to BaseWebLayout"
        #         )
        #         web_layout = None

        # if self._type == "web":
        #     self.user_interface_controller = WebUserInterfaceController(self, layout=web_layout)
        # else:
        #     ValueError("unknown type: '%s'" % self._type)

        # if "responsive" in self.config.get("experiment", "web_layout"):
        self.user_interface_controller = UserInterface(self)

        # Allows for session-specific saving of unlinked data.
        self._unlinked_random_name_part = uuid4().hex

        self.data_manager = DataManager(self)
        self.data_saver = DataSaver(self)

        self._condition = ""
        self._session = ""
        self.finished = False
        self.start_timestamp = None
        self.start_time = None

        if kwargs.get("basepath", None) is not None:
            self.log.warning("Usage of basepath is deprecated.")

        if kwargs.get("config_string", None) is not None:
            self.log.warning(
                (
                    "Usage of config_string is deprecated. Use "
                    + "alfred3.config.ExperimentConfig with the appropriate arguments instead."
                )
            )
        
        self.log.info(
            (
                f"Alfred {self.config.get('experiment', 'type')} experiment session initialized! "
                f"Alfred version: {self.alfred_version}, "
                f"Experiment title: {self.config.get('metadata', 'title')}, "
                f"Experiment version: {self.config.get('metadata', 'version')}"
            )
        )

    def start(self):
        self.root_section.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.log.info("Experiment.start() called. Session is starting.")
        self.user_interface_controller.start()

    def finish(self):
        if self.finished:
            self.log.warning(
                "Experiment.finish() called. Experiment was already finished. Leave Method"
            )
            return
        self.log.info("Experiment.finish() called. Session is finishing.")
        self.finished = True

        for page in self.root_section.all_pages.values():
            if not page.is_closed:
                page.close()

        if self.config.getboolean("general", "debug"):
            if self.config.getboolean("debug", "disable_saving"):
                return

        self.save_data()

        if self.config.getboolean("general", "transform_data_to_csv"):
            export_to_csv = threading.Thread(target=self.data_manager.export_data_to_csv, name="export")
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
        self.data_saver.main.save_with_all_agents(data=data, level=99)

        if self.root_section.unlinked_data():
            for agent in self.data_saver.unlinked.agents.values():
                unlinked_data = self.data_manager.get_unlinked_data(encrypt=agent.encrypt)
                self.data_saver.unlinked.save_with_agent(data=unlinked_data, name=agent.name, level=99)

    def get_page_data(self, page_uid):
        return self.data_manager.find_experiment_data_by_uid(uid=page_uid)

    @property
    def final_page(self):
        return self.root_section.final_page

    @final_page.setter
    def final_page(self, value):
        if not isinstance(value, page.PageCore):
            raise ValueError("Not a valid page.")

        self.root_section.final_page = value

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
    def exp_id(self):
        return self.config.get("metadata", "exp_id")

    @property
    def path(self):
        return str(self.config.expdir)

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

    @property
    def additional_data(self):
        return self.data_manager.additional_data
    
    @additional_data.setter
    def additional_data(self, data: dict):
        self.data_manager.additional_data = data

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

    def append(self, *items):
        for item in items:
            self.root_section.members["_content"].append(item)

    def __iadd__(self, other):
        self.append(other)
        return self

    # def __getattr__(self, name):
    #     return self.root_section.all_members_dict[name]

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
            return Fernet(key=key.encode())
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

    @deprecated("1.5", "2.0", __version__, "Use the attribute setter for :attr:`.final_page` instead.")
    def change_final_page(self, page):
        msg = "change_final_page is deprecated. Use the attribute setter for :attr:`.final_page` instead."
        self.log.warning(msg)
        self.root_section.append_item_to_finish_section(page)
    
    @deprecated("1.5", "2.0", __version__, "Use :attr:`.additional_data` instead.")
    def set_additional_data(self, key: str, value):
        """Shortcut for :meth:`DataManager.add_additional_data`.
        """
        self.log.warning("set_additional_data is deprecated. Use :attr:`.additional_data` instead.")
        self.data_manager.add_additional_data(key, value)

    @deprecated("1.5", "2.0", __version__, "Use :attr:`.additional_data` instead.")
    def get_additional_data(self, key: str):
        """Shortcut for :meth:`DataManager.get_additional_data_by_key`.
        """
        self.log.warning("get_additional_data is deprecated. Use :attr:`.additional_data` instead.")
        return self.data_manager.get_additional_data_by_key(key)