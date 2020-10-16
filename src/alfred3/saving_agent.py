"""Provides flexible saving capabilities for alfred3 experiments.
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>, Johannes Brachem <jbrachem@posteo.de>

"""

import queue
import logging
import threading
import time
import os
import json
import copy
import re

from abc import ABC, abstractmethod
from configparser import ConfigParser, SectionProxy
from pathlib import Path
from typing import Union, Tuple
from uuid import uuid4

import pymongo
import bson

from . import alfredlog
from .config import ExperimentConfig
from .exceptions import SavingAgentException, SavingAgentRunException

_logger = logging.getLogger(__name__)

# task = (priority, save_time, level, task_id, e, data, self, agent)
# def _do_saving(self, data: dict, name: str, level: int, data_time: float):


def _save_worker():
    """Takes a data dictionary and saving_agent_controller from the 
    global saving queue and calls the saving method of the controller.
    """
    try:
        while True:
            try:
                (_, t, lvl, _, event, data, sa_controller, agent_name,) = _queue.get_nowait()
            except queue.Empty:
                break
            sa_controller._do_saving(data=data, agent_name=agent_name, level=lvl, data_time=t)
            event.set()
            _queue.task_done()
    except Exception as e:
        _logger.critical("CRITICAL ERROR: Exception occured during save worker execution.")
        _logger.exception("")
        raise e


def _save_looper(sleeptime: int = 1):
    """Makes continuous calls to the :func:`_save_worker`.

    Args:
        sleeptime: Seconds between two calls to :func:`_save_worker`.
    """
    while not _quit_event.is_set():
        _save_worker()
        time.sleep(sleeptime)


def wait_for_saving_thread():
    """
    .. todo:: implement end_session of Logger into this method and execute for all experiment types!
    """
    # _logger.info("waiting until saving queue is empty. %s items left." % _queue.qsize())
    _queue.join()


# Setup an aplication wide saving thread
_queue = queue.PriorityQueue()
"""Global (application-wide) queue for saving tasks."""

_quit_event = threading.Event()
"""Event for signalling the :func:`_save_looper` to stop."""

_thread = threading.Thread(target=_save_looper, name="DataSaver")
"""Thread for executing the :func:`_save_looper` in the background."""

_thread.daemon = True
"""The significance of this flag is that the entire Python program exits 
when only daemon threads are left. (From threading documentation)"""

_thread.start()
"""The saving thread gets startet as soon as the alfred module is
imported."""

_logger.info("Global alfred3 saving thread started.")


class SavingAgent(ABC):
    """Base class for all saving agents. All saving agents must 
    inherit from :class:`SavingAgent` and define the method 
    :meth:`_save`.

    If you do not pass a value to the argument *name*, a name will be
    generated automatically, and a warning will be logged. The 
    generated name has the form::

        classname_time_uid

    Example::

        LocalSavingAgent_2020-08-05_t125518_6c8cda18e924486a9ab31a3072592d14

    Args:
        activation_level: The activation level is used by 
            :meth:`save_data` to determine whether data should be saved. 
            Generally, the lower the level, the more important is a 
            saving agent. You can think of the level as some kind of 
            hurdle to pass. (Defaults to 10)
        experiment: The experiment to which the saving agent belongs.
        name: The name of the saving agent. Will be used as a unique 
            identifier by saving agent controllers.
        use: Set to false, if this saving agent should not be used.
    """

    def __init__(
        self, activation_level: int = 10, experiment=None, name: str = None, encrypt: bool = False
    ):
        """Constructor method."""

        self.activation_level = activation_level
        self._experiment = experiment
        if self._experiment is None:
            raise SavingAgentException(
                "Saving Agents must be initialized with experiment instance."
            )

        self.log = self._init_log()

        self.name = name

        if name is None or name == "auto" or name == "":
            self.name = (
                type(self).__name__ + "_" + time.strftime("%Y-%m-%d_t%H%M%S") + "_" + uuid4().hex
            )
            self.log.debug(f"The name {self.name} was assigned automatically.")
        if name is None or name == "":
            self.log.warning(
                (
                    "No name provided for saving agent. Please provide a name via the 'name' argument. "
                    f"The name {self.name} was assigned automatically. If you want to assign the "
                    "name automatically, instantiate the SavingAgent with *name='auto'."
                )
            )

        self._lock = threading.Lock()
        self._latest_save_time = None
        self._fallback_agents = []
        self.encrypt = encrypt

        if self.encrypt and not self._experiment.secrets.get("encryption", "key"):
            raise ValueError(
                f"Encryption was turned on for {self}, but the experiment does not have an encryption key. Turn encryption off in the saving agent configuration, or provide an encryption key in secrets.conf."
            )

    def append_fallback(self, *args):
        """Appends saving agents to the list of fallback saving agents. 
        """

        for saving_agent in args:
            if not isinstance(saving_agent, SavingAgent):
                raise TypeError("Can only append children of SavingAgent.")

            self._fallback_agents.append(saving_agent)
            self.log.info(f"Fallback saving agent {saving_agent} added to {self}.")

    def save_data(self, data: dict, level: int, data_time: float = None) -> tuple:
        """Acquires a lock, performs some checks and calls :meth:`_save`.

        Will only save data, if:
        
        - *data_time* is newer than the latest previously saved data.
        - *level* is smaller than the agent's activation level.

        In case saving fails and the agent has fallbacks, more attempts 
        will be made with the fallback agents until one successful 
        saving proccess was performed or all fallback agents saved. If 
        the first fallback agent succeeds, the remaining fallback agents 
        will not be used.

        Args:
            data: Data to be saved.
            level: Incoming task level. If this is bigger than the
                agent's own activation level, the data will not be saved.
            data_time: Time of data snapshot in seconds since epoch. If
                no value is provided, the current time will be 
                inserted and a debug message will be logged.
        
        Returns:
            A tuple with two elements. The first value is a boolean, 
                which indicates whether or not data was saved. The 
                second value is a status string which gives more detail:
                
                * A value of "time" indicates that a newer data snapshot
                    was already present. 
                * A value of "error" indicates that an exception occured 
                    during saving. 
                * A value of "level" indicates that the task's level was
                    below the SavingAgent's activation level. 
                * A value of "success" indicates that data was saved 
                    successfully.
                * A value of "fallback" indicates that saving failed
                    initially, but succeed with at least one fallback
                    saving agent.
        """

        self._lock.acquire()

        if data_time is None:
            data_time = time.time()
            msg = f"No data_time provided in save_data call to {self}. Inserting current time."
            self.log.debug(msg)

        time_check = self._latest_save_time is None or self._latest_save_time < data_time
        if not time_check:
            msg = f"Data snapshot from {data_time} was not saved, because there was a newer one."
            self.log.info(msg)
            self._lock.release()
            return (False, "time")

        if level < self.activation_level:
            msg = (
                f"SavingAgent {self} was not run, because task level was smaller than "
                f"activation level ({level} < {self.activation_level})."
            )
            self.log.debug(msg)
            self._lock.release()
            return (False, "level")

        try:
            self._save(data)
        except Exception:
            self._lock.release()
            self.log.exception(f"Running SavingAgent {self} failed. Using fallback agents.")

            saved = False
            for agent in self._fallback_agents:
                saved, _ = agent.save_data(data=data, level=level, data_time=data_time)
                if saved:
                    break

            if saved:
                return (True, "fallback")
            else:
                return (False, "error")

        self.log.info(f"Running SavingAgent {self} succeeded.")
        self._latest_save_time = data_time
        self._lock.release()
        return (True, "success")

    @property
    def fallback_agents(self):
        return self._fallback_agents

    @property
    def exp(self):
        return self._experiment

    @abstractmethod
    def _save(self, data: dict):
        """Method for executing the actual saving task. Must be defined
        by all children of :class:`SavingAgent`.
        """
        pass

    def _init_log(self):
        loggername = self._prepare_logger_name()
        log = alfredlog.QueuedLoggingInterface(base_logger=__name__, queue_logger=loggername)
        log.session_id = self._experiment.config.get("metadata", "session_id")

        return log

    def _prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self._experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        return ".".join(name)


class LocalSavingAgent(SavingAgent):
    """A SavingAgent that writes data to a .json file on the disk.

    The most common use case is to append a SavingAgent to a 
    :class:`SavingAgentController`. You can also use a SavingAgent 
    individually by calling the :meth:`~LocalSavingAgent.save_data` 
    method.

    Args:
        filename: Filename for .json file. By default, the full filename
            will be combined with the associated experiment's session id
            to ensure that data for each session is saved. You can over-
            write the filename after initialization by assigning a value
            to the instance attribute. A '.json' suffix will be added
            automatically.
        filepath: Path to the directory in which to save the data.
        activation_level: The activation level is used by 
            :meth:`save_data` to determine whether data should be saved. 
            Generally, the lower the level, the more important is a 
            saving agent. You can think of the level as some kind of 
            hurdle to pass. (Defaults to 1)
        experiment: The experiment to which the saving agent belongs.
        name: Name of the saving agent instance.
        encrypt: Should data be encrypted before saving? (Currently
            only available for unlinked data)
    
    Attributes:
        filename: Full name of the .json file in which data is saved.
        save_directory: Directory containing the saved data files. If
            you set this directory with a path that is not absolute,
            it will be treated as a subdirectory of the experiment 
            directory.
        name: The name of the saving agent.
        activation_level: The saving agent's activation level.
        log: An instance of 
            :class:`alfred3.alfredlog.QueuedLoggingInterface` for logging.
    """

    def __init__(
        self,
        filename: str,
        directory: Union[str, Path],
        activation_level: int = 1,
        experiment=None,
        name: str = None,
        encrypt: bool = False,
    ):
        """Constructor method."""
        super().__init__(activation_level, experiment, name, encrypt)

        self.directory = directory
        self.filename = filename

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename: Union[str, Path]):
        f = Path(filename)
        if not f.suffix:
            f = Path(filename + ".json")
        self.directory / f  # to test, whether concatenation succeeds
        self._filename = f

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, path: Union[str, Path]):
        directory = Path(path)
        if not directory.is_absolute():
            directory = Path(self._experiment.path) / directory
        self._directory = directory

    def _check_directory(self):
        self.directory.mkdir(exist_ok=True, parents=True)
        if not self.directory.is_dir():
            raise RuntimeError(f"Save path {str(self.directory)} must be an directory.")

        if not os.access(str(self.directory), os.R_OK):
            raise RuntimeError(f"Save path {str(self.directory)} must be readable.")

        if not os.access(str(self.directory), os.W_OK):
            raise RuntimeError(f"Save path {str(self.directory)} must be writable.")

    def _save(self, data: dict):
        """Write data to file."""
        self._check_directory()
        with open(self.file, "w") as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @property
    def file(self):
        return self.directory / self.filename

    def __str__(self):
        return (
            f"<LocalSavingAgent [name: '{self.name}', path: '{str(self.file)}', "
            f"activation_level: '{str(self.activation_level)}']>"
        )


class AutoLocalSavingAgent(LocalSavingAgent):
    """Initializes a :class:`LocalSavingAgent` with an experiment.

    Args:
        experiment: An alfred experiment.
        config: A configparser section, containing the configuration for
            this agent.
    """

    def __init__(self, config: SectionProxy, experiment):
        super().__init__(
            filename=config.get("name"),
            directory=config.get("path"),
            activation_level=config.getint("level"),
            experiment=experiment,
            name=config.get("name"),
            encrypt=config.getboolean("encrypt", fallback=False),
        )


class MongoSavingAgent(SavingAgent):
    """A SavingAgent that writes data to a MongoDB collection.

    The most common use case is to append a SavingAgent to a 
    :class:`SavingAgentController`. You can also use a SavingAgent 
    individually by calling the :meth:`~MongoSavingAgent.save_data` 
    method.

    If you do not pass a value to the argument *name*, a name will be
    generated automatically, and a warning will be logged. The 
    generated name has the form::

        classname_time_uid

    Example::

        MongoSavingAgent_2020-08-05_t125518_6c8cda18e924486a9ab31a3072592d14

    By defining a custom identifier, you can change the SavingAgent's
    behavior, e.g. from saving a new document for every experiment 
    session to saving only one document for the experiment::

        agent = MongoSavingAgent(...)
        agent.identifier = {"exp_id": agent.exp.exp_id}

    Args:
        client: An active MongoClient.
        db: Name of the database to use.
        collection: Name of the database collection to use.
        activation_level: The activation level is used by 
            :meth:`save_data` to determine whether data should be saved. 
            Generally, the lower the level, the more important is a 
            saving agent. You can think of the level as some kind of 
            hurdle to pass. (Defaults to 1)
        experiment: The experiment to which the saving agent belongs.
        name: Name of the saving agent instance.
        encrypt: Should data be encrypted before saving? (Currently
            only available for unlinked data)

    Attributes:
        name: The name of the saving agent.
        activation_level: The saving agent's activation level.
        log: An instance of 
            :class:`alfred3.alfredlog.QueuedLoggingInterface` for logging.
        identifier: A filter dictionary that allows for
            fine-grained control of the SavingAgent's saving behavior.
            The filter will be used to query the connected MongoDB.
            If a document is found, it will be replaced with the data.
            If no document is found, the data will be inserted as a new
            document. Defaults to an instance-specific (and therefore
            session-specific) ObjectId.
    """

    client_pattern = re.compile(r"host=\['(?P<host>.+):(?P<port>\d+)'\]")

    def __init__(
        self,
        client: pymongo.MongoClient,
        database: str,
        collection: str,
        activation_level: int = 1,
        experiment=None,
        name: str = None,
        encrypt: bool = False,
    ):
        """Constructor method."""
        super().__init__(
            activation_level=activation_level, experiment=experiment, name=name, encrypt=encrypt
        )
        self._mc = client
        self._db = self._mc[database]
        self._col = self._db[collection]
        self.doc_id = uuid4().hex

        self._identifier = {"_id": self.doc_id}

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, identifier: dict):
        if not isinstance(identifier, dict):
            raise ValueError("Identifier must be a dictionary.")
        else:
            self._identifier = identifier

    def _save(self, data):
        f = self.identifier
        data.update(f)
        data["_id"] = self.doc_id

        if self._col.find_one(filter=f):
            self._col.find_one_and_replace(filter=f, replacement=data)
        else:
            self._col.insert_one(document=data)

        try:
            data.pop("_id")
        except KeyError:
            pass

        check = self._col.find_one(filter=f)
        doc_id = check.pop("_id")

        if not check == data:
            raise SavingAgentRunException("Failed to validate data saving.")

        return doc_id

    @property
    def client(self):
        """The agent's :class:`pymongo.MongoClient`."""
        return self._mc

    @property
    def db(self):
        """The agent's :class:`pymongo.database.Database`."""
        return self._db

    @property
    def col(self):
        """The agent's :class:`pymongo.collection.Collection`."""
        return self._col

    def check_equality(self, agent) -> bool:
        a1 = (self.client_info(self.client), self.db.name, self.col.name)
        a2 = (self.client_info(agent.client), agent.db.name, agent.col.name)

        return a1 == a2

    @classmethod
    def client_info(cls, client) -> tuple:
        """Returns a tuple (host, port) for a MongoClient."""
        m = cls.client_pattern.search(str(client))
        chost, cport = m.group("host"), m.group("port")
        return chost, cport

    @classmethod
    def validate_client(cls, client, config=None, host=None, port=None):
        chost, cport = cls.client_info(client)

        if config:
            if not (config.get("host") == chost and config.get("port") == cport):
                return False
            else:
                return True
        elif host and port:
            if not (host == chost and port == cport):
                return False
            else:
                return True
        elif (host and not port) or (port and not host):
            raise ValueError("Both port and host are needed for comparison.")

    def __str__(self):
        msg = (
            f"<MongoSavingAgent [name: '{self.name}', host: {self._mc.host}, database: "
            f"{self._db.name}.{self._col.name}, activation level: '{self.activation_level}']>"
        )

        return msg


class AutoMongoSavingAgent(MongoSavingAgent):
    """Initializes a :class:`MongoSavingAgent` with auto configuration.

    The agent extracts configuration automatically from a 
    :class:`configparser.SectionProxy`. If the agent receives no client,
    it initializes its own client.

    The *config*  needs to define the following fields:

    - host (optional, if a *client* is passed)
    - port (optional, if a *client* is passed)
    - user (optional, if a *client* is passed)
    - password (optional, if a *client* is passed)
    - use_ssl (optional, if a *client* is passed)
    - ca_file_path (optional, if a *client* is passed)
    - database
    - collection
    - level
    - name

    Args:
        config: A :class:`configparser.SectionProxy` with appropriate
            configuration.
        client: A :class:`pymongo.MongoClient` for the agent. Make sure
            that the client's connection has read and write privileges
            for the specified collection.
        experiment: An alfred experiment.
     """

    def __init__(
        self, config: SectionProxy, client: pymongo.MongoClient = None, experiment=None,
    ):

        if not client:
            client = AutoMongoClient(config=config)

        if not self.validate_client(client, config):
            raise ValueError("The client and configuration contain different values for 'host'.")

        super().__init__(
            client=client,
            database=config.get("database"),
            collection=config.get("collection"),
            activation_level=config.getint("level"),
            experiment=experiment,
            name=config.get("name"),
            encrypt=config.getboolean("encrypt", fallback=False),
        )


class MongoManager:

    """Allows for the easy initialization of multiple MongoSavingAgents
    with overlapping configuration and shared MongoClients.

    Args:
        experiment: Alfred experiment.
    """

    def __init__(self, experiment):
        self.exp = experiment
        self.clients = []

    def _init_client(self, config: SectionProxy):
        ca_file = config.get("ca_file_path") if config.getboolean("use_ssl") else None
        client = pymongo.MongoClient(
            host=config.get("host"),
            port=config.getint("port"),
            username=config.get("user"),
            password=config.get("password"),
            tls=config.getboolean("use_ssl"),
            tlsCAFile=ca_file,
            authSource=config.get("auth_source"),
        )
        return client

    def init_agent(
        self,
        section: str,
        fill_section: str = None,
        agent_class=AutoMongoSavingAgent,
        fallbacks: list = None,
        config_name: str = "secrets",
    ):
        """Economically initializes a MongoSavingagent.

        * Configuration from *section* will be completed with config
            from *fill_section*, such that you only need to specify
            changing information in your configuration file.
        
        * If appropriate, an existing MongoClient will be used for the
            new agent in order to save resources.
        
        Args:
            agent_class: The class that will be used to instantiate
                a saving agent.
            section: Name of section with configuration information.
            fill_section: Name of section with configuration for
                filling in information that is missing in *section*. 
                Defaults to None.
            fallbacks: List of section names (str) for configuration
                of fallback agents. These must be fully specified.
                Defaults to None.
            config_name: Name of the experiment's attribute with the
                configuration object to be used. Defaults to 'secrets'.
        """
        parser = getattr(self.exp, config_name)

        if not isinstance(parser, ExperimentConfig):
            raise ValueError("No experiment config available under the given name.")

        if fill_section:
            conf = parser.combine_sections(fill_section, section)
        else:
            conf = parser[section]

        client = self._available_client(conf)
        agent = agent_class(config=conf, client=client, experiment=self.exp)

        if fallbacks:
            for fb_section_name in fallbacks:
                if parser.getboolean(fb_section_name, "use"):
                    fb_agent = self.init_agent(
                        agent_class=agent_class, section=fb_section_name, config_name=config_name
                    )
                    agent.append_fallback(fb_agent)

        return agent

    def _available_client(self, config: SectionProxy):
        """Returns a fitting MongoClient. 
        
        If a fitting client is already present in the MongoManager's
        client list, that client will be returned.

        Else, a new client will be instantiated, returned and appended
        to the internal client list.
        """

        for client in self.clients:
            if AutoMongoSavingAgent.validate_client(client, config):
                return client

        new_client = self._init_client(config)
        self.clients.append(new_client)

        return new_client


class SavingAgentController:
    """Orchestrates the  operation of multiple SavingAgents.

    Usage:
    Initiate the SavingAgentController with an alfred experiment and
    append saving agents using :meth:`~SavingAgentController.append`.

    To prevent data loss when saving errors occur, append at least one 
    failure saving agent using 
    :meth:`~SavingAgentController.append_failure_agent`. The failure 
    agents will be employed only when all fallback agents of a particular
    saving agents fail.

    Args:
        experiment: An alfred experiment.
    """

    def __init__(self, experiment):
        """Constructor method."""

        self._agents = {}
        self._failure_agents = {}
        self._experiment = experiment
        self.log = self._init_log()

    def append(self, saving_agent: SavingAgent):
        """Appends a saving agent to the controller."""
        if not isinstance(saving_agent, SavingAgent):
            raise TypeError("Can only add children of SavingAgent.")

        if saving_agent.name in self.agents:
            raise ValueError("SavingAgent name must be unique.")

        self._agents[saving_agent.name] = saving_agent

        if saving_agent.activation_level <= 1:
            self.log.info(f"Continuous SavingAgent {saving_agent} added to experiment")
        elif saving_agent.activation_level > 1:
            self.log.info(f"SavingAgent {saving_agent} added to experiment")

    @property
    def agents(self):
        return self._agents

    def append_failure_agent(self, saving_agent: SavingAgent):
        """Appends a SavingAgent to the list of failure agents.
        
        Failure SavingAgents are the last resort in order to avoid 
        data loss. The failure SavingAgents get called when a 
        SavingAgent and all its fallback agents fail.

        Args:
            saving_agent: A saving agent instance.
        """

        if not isinstance(saving_agent, SavingAgent):
            raise TypeError("Can only add children of SavingAgent.")

        if saving_agent.name in self._failure_agents:
            raise ValueError("SavingAgent name must be unique.")

        self._failure_agents[saving_agent.name] = saving_agent

    def remove_agent(self, name: str):
        """Removes a saving agent from the controller

        Args:
            name (str): Name of the saving agent to be removed.
        """
        self.agents.pop(name)

    def save_with_all_agents(self, data: dict, level: int, sync: bool = False):
        """Puts saving tasks into the app-wide saving queue for all 
        agents attached to the controller. 
        
        Args:
            data: Data to be saved.
            level: Level of saving task. If the task level is 
                below a saving agent's activation level, it will not
                be saved.
            sync: Whether to synchronise the task. If
                True, the experiment will continue only after the task
                was completed. Defaults to False.
        """
        for agent in self.agents.values():
            self._queue_task(data=data, level=level, agent_name=agent.name, sync=sync)

    def save_with_agent(self, data: dict, name: str, level: int, sync: bool = False):
        """Puts a saving task in to the app-wide saving queue for the
        agent *name*.

        Args:
            data: Data to be saved.
            level: Level of saving task. If the task level is 
                below a saving agent's activation level, it will not
                be saved.
            name: Name of the saving agent.
            sync: Whether to synchronise the task. If
                True, the experiment will continue only after the task
                was completed. Defaults to False.
        """
        self._queue_task(data=data, level=level, agent_name=name, sync=sync)

    def _queue_task(self, data: dict, level: int, agent_name: str, sync: bool = False):
        """Puts a saving task into the app-wide saving queue.
        
        Args:
            data: Data to be saved.
            level: Level of saving task. If the task level is 
                below a saving agent's activation level, it will not
                be saved.
            agent_name: Name of the SavingAgent to be used for this task.
            sync: Whether to synchronise the task. If
                True, the experiment will continue only after the task
                was completed. Defaults to False.
        """

        save_time = time.time()
        task_id = uuid4()

        priority = 1 if sync else 5
        e = threading.Event()

        task = (priority, save_time, level, task_id, e, data, self, agent_name)
        _queue.put(task)
        if sync:
            e.wait()

    def _do_saving(self, data: dict, agent_name: str, level: int, data_time: float):
        """Starts the execution of a task with the given saving agent. 
        
        If the agent and its fallbacks fail, the SavingAgentController 
        will save the data using ALL available failure saving agents.
        """

        agent = self.agents[agent_name]
        saved, _ = agent.save_data(data=data, level=level, data_time=data_time)

        if not saved:
            self.log.warning(
                f"Saving with {agent} failed. Attempting to save with failure saving agent now."
            )

            any_failure_saved = False
            for failure_agent in self._failure_agents.values():
                failure_saved, _ = failure_agent.save_data(
                    data=data, level=level, data_time=data_time
                )
                if failure_saved:
                    any_failure_saved = True

            if not any_failure_saved:
                msg = (
                    "CRITICAL ERROR. SAVING FAILED. "
                    "No failure SavingAgent succeeded in saving. Saving task was not completed."
                )
                self.log.critical(msg)

    def run_saving_agents(self, level: int, sync: bool = False):
        """Automatically gets experimental data, inserts the current
        time in seconds since epoch as 'save_time' and saves with the
        'main' saving agent group.

        Provided under this name mainly for backwards compatibility.
        
        The methods :meth:`save_with_group` and :meth:`save_with_agent`
        are the recommended replacements. They don't guess the intended
        saving agent group and never don't modify the data.

        Args:
            level (int): Level of saving task. If the task level is 
                below a saving agent's activation level, it will not
                be saved.
            sync (bool, optional): Whether to synchronise the task. If
                True, the experiment will continue only after the task
                was completed. Defaults to False.
        """

        data = self._experiment.data_manager.get_data()
        data["save_time"] = time.time()

        self.save_with_all_agents(data=data, level=level, sync=sync)

    def _init_log(self):
        loggername = self._prepare_logger_name()
        log = alfredlog.QueuedLoggingInterface(base_logger=__name__, queue_logger=loggername)
        log.session_id = self._experiment.config.get("metadata", "session_id")

        return log

    def _prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self._experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        return ".".join(name)


class CodebookMixin:
    @staticmethod
    def _identify_duplicates_and_update(old_data: dict, new_data: dict) -> Tuple[int, dict]:
        """Updates a nested dictionary with values from another nested dictionary.

        If duplicate keys with different values are encountered, the keys
        will be mutated to include the term '_duplicate' plus a counter
        of duplicates. The value dicts will receive an additional field 
        of ``"duplicate_identifier": True``.

        Example::

            a = {"exp_title": "test", 
                "codebook": {
                    "name1": {"instruction": "instr1"}
                    },
                }
            
            b = {
                "exp_title": "test",
                "codebook": {
                    "name1": {"instruction": "instr2", "desription": "desc"},
                    "name2": {"instruction": "instr2"},
                },
            }

            counter, updated_data = duplicate_save_update(old_data=a, new_data=b)

            # counter = 2
            # updated_data =  { 'name1_duplicate1': {'duplicate_identifier': True, 'instruction': 'instr1'},
                                'name1_duplicate2': {'desription': 'desc',
                                                    'duplicate_identifier': True,
                                                    'instruction': 'instr2'},
                                'name2': {'instruction': 'instr2'}}



        Returns:
            A tuple containing the duplicate counter (total number of
            affected key-value pairs in the updated dictionary) and the
            updated dictionary.
        """
        duplicate_entries = 0

        update_entries = []
        for identifier, new_element in new_data.items():
            try:
                duplicate_elements = 0
                old_element = old_data[identifier]
                if not old_element == new_element:
                    new_element["duplicate_identifier"] = True
                    old_element["duplicate_identifier"] = True
                    old_data.pop(identifier)

                    duplicate_entries += 2
                    duplicate_elements += 1

                    entry2 = {f"{identifier}_duplicate{duplicate_elements}": new_element}

                    update_entries.append({identifier: old_element})
                    update_entries.append(entry2)
            except KeyError:
                update_entries.append({identifier: new_element})

        for entry in update_entries:
            old_data.update(entry)

        return duplicate_entries, old_data


class CodebookLocalSavingAgent(AutoLocalSavingAgent, CodebookMixin):
    def _save(self, data: dict):

        try:
            with open(self.file, "r") as f:
                existing_data = json.load(f)

            _, updated_codebook = self._identify_duplicates_and_update(
                old_data=existing_data["codebook"], new_data=data["codebook"]
            )

            existing_data["codebook"] = updated_codebook

            super()._save(data=existing_data)
        except FileNotFoundError:
            super()._save(data=data)


class CodebookMongoSavingAgent(AutoMongoSavingAgent, CodebookMixin):
    def _save(self, data: dict):

        f = self.identifier
        existing_data = self._col.find_one(filter=f)
        if existing_data:
            self.doc_id = existing_data["_id"]

        try:
            _, updated_codebook = self._identify_duplicates_and_update(
                old_data=existing_data["codebook"], new_data=data["codebook"]
            )
            existing_data["codebook"] = updated_codebook
            # self.col.find_one_and_replace(filter=f, replacement=data)
            super()._save(data=existing_data)
        except (KeyError, TypeError):
            super()._save(data=data)


class AutoMongoClient(pymongo.MongoClient):
    """Constructs a :class:`pymongo.MongoClient` directly from an alfred
    configuration section.
    
    """

    def __init__(self, config: SectionProxy, **kwargs):
        host = config.get("host")
        port = config.getint("port")
        username = config.get("user")
        password = config.get("password")
        tls = config.getboolean("use_ssl")
        tlsCAFile = config.get("ca_file_path") if tls else None
        authSource = config.get("auth_source")
        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            authSource=authSource,
            tls=tls,
            tlsCAFile=tlsCAFile,
            **kwargs,
        )
