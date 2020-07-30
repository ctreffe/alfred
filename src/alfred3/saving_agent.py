# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

"""
from __future__ import absolute_import

import json
import os
import queue
import threading
import time
import uuid
import traceback
import logging
from abc import ABCMeta, abstractmethod
from builtins import object
from configparser import SectionProxy
from typing import Union, Type

import pymongo
from future import standard_library
from future.utils import with_metaclass

import alfred3.settings

from .exceptions import SavingAgentException, SavingAgentRunException
from . import alfredlog

standard_library.install_aliases()


_logger = logging.getLogger(__name__)


def _save_worker():
    try:
        while True:
            try:
                (_, data_time, level, _, event, data, sac) = _queue.get_nowait()
            except queue.Empty:
                break
            sac._do_saving(data, data_time, level)
            event.set()
            _queue.task_done()
    except Exception as e:
        _logger.critical("MOST OUTER EXCEPTION IN SAVE WORKER!!! {}".format(e))


def _save_looper(sleeptime=1):
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
_quit_event = threading.Event()


if alfred3.settings.experiment.type == "qt-wk":
    _logger.info("Starting saving thread for qt-wk experiment.")
elif alfred3.settings.experiment.type == "web":
    _logger.info("Starting global saving thread for web experiments.")

_thread = threading.Thread(target=_save_looper, name="DataSaver")
_thread.daemon = True
_thread.start()


class SavingAgentController(object):
    def __init__(self, experiment):
        self._latest_data_time = None
        self._lock = threading.Lock()
        self._experiment = experiment
        loggername = self.prepare_logger_name()
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__, queue_logger=loggername)
        self.log.session_id = self._experiment.config.get("metadata", "session_id")

        self._agents = []
        """run agents that run in normaly"""
        self._failure_agents = []
        """agents that run if running a normal agent fails """

        if self._experiment.config.getboolean(
            "general", "debug"
        ) and self._experiment.config.getboolean("debug", "disable_saving"):
            self.log.warning("Saving has been disabled!")
        else:
            self.initialize_local_agents(config=self._experiment.config)
            self.initialize_db_agents(self._experiment.secrets, AutoMongoSavingAgent)
            self.initialize_db_agents(self._experiment.secrets, AutoCouchDBSavingAgent)

        self.init_backwards_compatible()

        # if alfred3.settings.debugmode and alfred3.settings.debug.disable_saving:
        #     _logger.warning("Saving has been disabled!", self._experiment)
        # else:
        #     self.init_saving_agents()

    def init_backwards_compatible(self):
        """Provides backwards compatibility.
        
        - Initializes DB saving agents defined in *config.conf* and
        logs warnings.
        """
        # for backwards compatibility
        self.initialize_db_agents(self._experiment.config, AutoMongoSavingAgent)
        self.initialize_db_agents(self._experiment.config, AutoCouchDBSavingAgent)

        if self._experiment.config.getboolean(
            "mongo_saving_agent", "use"
        ) or self._experiment.config.getboolean("couchdb_saving_agent", "use"):
            self.log.warning(
                (
                    "Defining a 'mongo_saving_agent' in 'config.conf' is deprecated. "
                    + "Define it in 'secrets.conf' instead, to keep your database credentials safe."
                )
            )

    def initialize_local_agents(self, config: Union[SectionProxy, dict]) -> bool:
        """Initializes local saving agents.

        Initialization is tried for the following versions, depending
        on configuration in *config*.

        1. Failure save agent
        2. Usual local saving agent
        3. Fallback local saving agent
        4. Level 2 Fallback local saving agent
        
        Args:
            config: Normally, :attr:`experiment.config` (parsed from config.conf)
        
        Returns:
            bool: *False*, if any agent was not added succesfully (else 
                *True*).
        """

        # 1: add failure agent
        failed_to_add_failure_agent = self.init_agent(
            agent_class=AutoLocalSavingAgent,
            agent_config=config.get_section("failure_local_saving_agent"),
            failure_agent=True,
        )

        # 2: add normal agent
        failed_to_add_local_agent = self.init_agent(
            agent_class=AutoLocalSavingAgent, agent_config=config.get_section("local_saving_agent")
        )

        # 3: add fallback agent
        failed_to_add_local_fallback = False
        if failed_to_add_local_agent:
            failed_to_add_local_fallback = self.init_agent(
                agent_class=AutoLocalSavingAgent,
                agent_config=config.get_section("fallback_local_saving_agent"),
            )

        # 4: add level 2 fallback
        failed_to_add_local_fallback2 = False
        if failed_to_add_local_fallback:
            failed_to_add_local_fallback2 = self.init_agent(
                agent_class=AutoLocalSavingAgent,
                agent_config=config.get_section("fallback_local_saving_agent"),
            )

        if any(
            [
                failed_to_add_failure_agent,
                failed_to_add_local_agent,
                failed_to_add_local_fallback,
                failed_to_add_local_fallback2,
            ]
        ):
            all_ok = False
        else:
            all_ok = True

        return all_ok

    def initialize_db_agents(self, config: Union[SectionProxy, dict], agent_class):
        """Initializes MongoSavingAgents.
        
        Args:
            config: Normally, :attr:`experiment.secrets` (parsed from 
                *secrets.conf*)

            bool: *False*, if any agent was not added succesfully (else 
                *True*).
        """

        section_name = f"{agent_class.handle}_saving_agent"
        fallback_name = f"fallback_{section_name}"

        failed_to_add = self.init_agent(
            agent_class=agent_class, agent_config=config.get_section(section_name)
        )

        failed_to_add_fallback = False
        if failed_to_add:
            failed_to_add_fallback = self.init_agent(
                agent_class=agent_class, agent_config=config.get_section(fallback_name),
            )

        if any([failed_to_add, failed_to_add_fallback]):
            all_ok = False
        else:
            all_ok = True

        return all_ok

    def initialize_agents(self, config):
        """Initializes the standard saving agents from a configuration
        object.

        If ANY agent fails to initialize, initialization of ALL fallback
        agents is tried.
        """

        # 1: add failure agent
        failed_to_add_failure_agent = self.init_agent(
            agent_class=AutoLocalSavingAgent,
            agent_config=config.get_section("failure_local_saving_agent"),
            failure_agent=True,
        )

        # 2: add normal agents
        failed_to_add_local_agent = self.init_agent(
            agent_class=AutoLocalSavingAgent, agent_config=config.get_section("local_saving_agent")
        )

        failed_to_add_mongo_agent = self.init_agent(
            agent_class=AutoMongoSavingAgent, agent_config=config.get_section("mongo_saving_agent")
        )

        failed_to_add_couch_agent = self.init_agent(
            agent_class=AutoCouchDBSavingAgent,
            agent_config=config.get_section("couchdb_saving_agent"),
        )

        # 3: add fallback for normal agents
        if any([failed_to_add_local_agent, failed_to_add_mongo_agent, failed_to_add_couch_agent]):
            failed_to_add_local_fallback = False

            failed_to_add_local_fallback = self.init_agent(
                agent_class=AutoLocalSavingAgent,
                agent_config=config.get_section("fallback_local_saving_agent"),
            )

            self.init_agent(
                agent_class=AutoMongoSavingAgent,
                agent_config=config.get_section("fallback_mongo_saving_agent"),
            )

            self.init_agent(
                agent_class=AutoCouchDBSavingAgent,
                agent_config=config.get_section("fallback_couchdb_saving_agent"),
            )

        # 4: add level 2 fallback
        if failed_to_add_local_fallback:
            self.init_agent(
                agent_class=AutoLocalSavingAgent,
                agent_config=config.get_section("fallback_local_saving_agent"),
            )

        # 5: check if self._agents is empty
        if not self._agents and not self._experiment.config.getboolean("debug", "disable_saving"):
            self.log.critical(
                "Session abort! List of SavingAgents is empty, but saving is not disabled."
            )
            raise SavingAgentException(
                "Session abort! List of SavingAgents is empty, but saving is not disabled."
            )

    def init_agent(
        self, agent_class, agent_config: Union[SectionProxy, dict], failure_agent: bool = False,
    ):
        """Adds a generic child of :class:`SavingAgent` to the instance.

        The agent class passed to the argument ``agent`` must be 
        implemented with the ability to extract its configuration
        directly from a dictionary or :class:`configparser.SectionProxy`.

        Args:
            agent: A child class of :class:`SavingAgent`.
            agent_config: A config section or dictionary
            containing the init parameters for the agent.
            failure_agent (optional): Should be set to `True`, if the
                agent to be initialized is a failure saving agent,
                i.e. an agent that is used in case of the failure of
                another agent. Defaults to False.

        Raises:
            SavingAgentException: If the option ``assure_initialization``
                in ``agent_config`` is ``True``, this exception is raised
                if any exception occurs during agent initialization.

        Returns:
            bool: An indicator for a failure during agent initialization.
                `False`, if everything went as expected, `True` if
                the agent could not successfully be added.
            None: If *config* contains a value of "use = false", the 
                method just returns *None*.
        """

        failed_to_add = False

        if not agent_config or not agent_config.getboolean("use"):
            return None

        try:
            agent_instance = agent_class(agent_config=agent_config, experiment=self._experiment)
            if failure_agent:
                self.add_failure_saving_agent(saving_agent=agent_instance)
            else:
                self.add_saving_agent(saving_agent=agent_instance)

        except Exception as e:
            if agent_config.getboolean("assure_initialization"):
                msg = f"Critical initialization abort! Initializing {agent_class} based on >{agent_config._name}< failed with the follwing exception: {traceback.format_exc()}"

                self.log.critical(msg)
                raise SavingAgentException(msg)
            else:
                failed_to_add = True
                msg = f"Initializing {agent_instance} based on >{agent_config._name}< failed with the follwing exception: {e}"
                self.log.warning(msg)

        return failed_to_add

    def add_saving_agent(self, saving_agent):
        if not isinstance(saving_agent, SavingAgent):
            raise TypeError

        self._agents.append(saving_agent)
        if saving_agent.activation_level <= 1:
            self.log.info(f"Continuous SavingAgent {saving_agent} added to experiment")
        elif saving_agent.activation_level > 1:
            self.log.info(f"SavingAgent {saving_agent} added to experiment")

    def add_failure_saving_agent(self, saving_agent):
        if not isinstance(saving_agent, SavingAgent):
            raise TypeError

        self._failure_agents.append(saving_agent)

    def run_saving_agents(self, level, sync=False):

        priority = 1 if sync else 5
        e = threading.Event()  # initialise empty threading event
        data = (
            self._experiment.data_manager.get_data()
        )  # dictionary of the .json data file of current session
        data["save_time"] = time.time()  # set data["save_time"] to current time
        _queue.put((priority, time.time(), level, str(uuid.uuid4()), e, data, self))
        if sync:
            e.wait()

    def _do_saving(self, data, data_time, level):
        self._lock.acquire()
        if self._latest_data_time is None or self._latest_data_time < data_time:
            failed = False
            for agent in self._agents:
                if agent.activation_level <= level:
                    try:
                        agent.save_data(data, level)
                        self._latest_data_time = data_time
                        if level <= 1:
                            self.log.debug(f"Running SavingAgent {agent} succeeded")
                        else:
                            self.log.info(f"Running SavingAgent {agent} succeeded")
                    except Exception as e:
                        failed = True
                        self.log.error(f"Running SavingAgent {agent} failed with error: {e}")
            if failed:
                for agent in self._failure_agents:
                    try:
                        agent.save_data(data, 1000)
                        self._latest_data_time = data_time
                        self.log.info(f"Running Backup SavingAgent {agent} succeeded")
                    except Exception as e:
                        self.log.critical(
                            f"Running Backup SavingAgent {agent} failed with error: {e}"
                        )
        else:
            self.log.info(
                f"Data snapshot taken at {data_time} will not be saved because a newer one ({self._latest_data_time}) was already saved."
            )
        self._lock.release()

    def prepare_logger_name(self) -> str:
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


class SavingAgent(with_metaclass(ABCMeta, object)):
    def __init__(self, activation_level=10, experiment=None):
        self.activation_level = activation_level

        if experiment is None:
            raise SavingAgentException(
                "Saving Agents must be initialized with experiment instance."
            )

        self._experiment = experiment
        self._lock = threading.Lock()

    def save_data(self, data, level):

        self._lock.acquire()
        try:
            if self.activation_level <= level:
                self._save(data)
        except Exception as e:
            self._lock.release()
            raise e
        self._lock.release()

    @abstractmethod
    def _save(self, data):
        pass


class LocalSavingAgent(SavingAgent):
    def __init__(self, filename, filepath, activation_level=1, experiment=None):
        super(LocalSavingAgent, self).__init__(activation_level, experiment)

        if not os.path.isabs(filepath):
            filepath = os.path.join(experiment.path, filepath)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        if not os.path.isdir(filepath):
            raise RuntimeError("save path '%s' must be an directory" % filepath)
        if not os.access(filepath, os.W_OK):
            raise RuntimeError("save path '%s' must be writable" % filepath)

        filename = "%s_%s_%s.json" % (
            time.strftime("%Y-%m-%d_t%H%M%S"),
            filename,
            self._experiment.session_id,
        )
        self._file = os.path.join(filepath, filename)

        if os.path.exists(self._file):
            if not os.access(self._file, os.W_OK) or not os.access(self._file, os.R_OK):
                raise RuntimeError("File '%s' must be readable and writable" % self._file)

    def _save(self, data):
        try:
            with open(self._file, "w") as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return "<LocalSavingAgent [path: %s]>" % self._file


class AutoLocalSavingAgent(LocalSavingAgent):
    """A wrapper around :class:`LocalSavingAgent` that parses 
    initialization settings directly from a config section.

    Args:
        agent_config: A config section or dictionary
            containing the init parameters for the parent class.
    """

    def __init__(self, agent_config: Union[SectionProxy, dict], experiment):
        filename = agent_config.get("name")
        filepath = agent_config.get("path")
        level = agent_config.getint("level")
        super().__init__(
            filename=filename, filepath=filepath, activation_level=level, experiment=experiment
        )


class CouchDBSavingAgent(SavingAgent):

    handle = "couch"

    def __init__(self, url, database, activation_level=10, experiment=None):
        import couchdb  # pylint: disable=import-error

        super(CouchDBSavingAgent, self).__init__(activation_level, experiment)

        try:
            self._server = couchdb.Server(url=url)
            self._db = self._server[database]
        except Exception as e:
            raise SavingAgentException("Type: %s" % type(e))

        self._doc_id = self._experiment.session_id
        self._doc_rev = None

    def _save(self, data):
        if self._doc_rev:
            data["_rev"] = self._doc_rev

        try:
            self._db[self._doc_id] = data
            self._doc_rev = data["_rev"]
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return "<CouchDBSavingAgent [url: %s, database: %s]>" % (
            self._server.resource.url,
            self._db.name,
        )


class AutoCouchDBSavingAgent(CouchDBSavingAgent):
    """A wrapper around :class:`CouchDBSavingAgent` that parses 
    initialization settings directly from a config section.

    Args:
        agent_config: A config section or dictionary
            containing the init parameters for the parent class.
    """

    def __init__(self, agent_config: Union[SectionProxy, dict], experiment):
        url = agent_config.get("url")
        database = agent_config.get("database")
        activation_level = agent_config.getint("level")

        super().__init__(
            url=url, database=database, activation_level=activation_level, experiment=experiment,
        )


class MongoSavingAgent(SavingAgent):

    handle = "mongo"

    def __init__(
        self,
        host,
        port,
        database,
        collection,
        user,
        password,
        use_ssl,
        ca_file_path,
        activation_level=10,
        experiment=None,
        auth_source="admin",
    ):
        super(MongoSavingAgent, self).__init__(activation_level, experiment)

        if use_ssl and os.path.isfile(ca_file_path):  # if self-signed ssl cert is used
            self._mc = pymongo.MongoClient(
                host=host,
                port=port,
                username=user,
                password=password,
                ssl=use_ssl,
                ssl_ca_certs=ca_file_path,
                authSource=auth_source,
            )
        elif use_ssl:  # if commercial ssl certificate is used
            self._mc = pymongo.MongoClient(
                host=host,
                port=port,
                username=user,
                password=password,
                ssl=use_ssl,
                authSource=auth_source,
            )
        else:  # if no ssl encryption is used
            self._mc = pymongo.MongoClient(
                host=host, port=port, username=user, password=password, authSource=auth_source
            )

        self._db = self._mc[database]
        # if not self._db.authenticate(user, password):
        #     raise RuntimeError("Could not authenticate with %s.%s" % (host, database))

        self._col = self._db[collection]
        self._doc_id = self._experiment.session_id

    def _save(self, data):

        try:
            data["_id"] = self._doc_id
            self._col.save(data)
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return "<MongoSavingAgent [host: %s, database: %s.%s]>" % (
            self._mc.host,
            self._db.name,
            self._col.name,
        )


class AutoMongoSavingAgent(MongoSavingAgent):
    """A wrapper around :class:`MongoSavingAgent` that parses 
    initialization settings directly from a config section.

    Args:
        agent_config: A config section or dictionary
            containing the init parameters for the parent class.
    """

    def __init__(self, agent_config: Union[SectionProxy, dict], experiment):
        host = agent_config.get("host")
        port = agent_config.getint("port")
        database = agent_config.get("database")
        collection = agent_config.get("collection")
        user = agent_config.get("user")
        password = agent_config.get("password")
        use_ssl = agent_config.get("use_ssl")
        ca_file_path = agent_config.get("ca_file_path")
        auth_source = agent_config.get("auth_source")
        activation_level = agent_config.getint("level")

        super().__init__(
            host=host,
            port=port,
            database=database,
            collection=collection,
            user=user,
            password=password,
            use_ssl=use_ssl,
            ca_file_path=ca_file_path,
            activation_level=activation_level,
            experiment=experiment,
            auth_source=auth_source,
        )
