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
from abc import ABCMeta, abstractmethod
from builtins import object

import pymongo
from future import standard_library
from future.utils import with_metaclass

import alfred3.settings

from . import alfredlog
from .exceptions import SavingAgentException, SavingAgentRunException

standard_library.install_aliases()


_logger = alfredlog.getLogger(__name__)


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
        import logging
        logger = logging.getLogger(__name__)
        logger.critical("MOST OUTER EXCEPTION IN SAVE WORKER!!! {}".format(e))


def _save_looper(sleeptime=1):
    while not _quit_event.is_set():
        _save_worker()
        time.sleep(sleeptime)


def wait_for_saving_thread():
    '''
    .. todo:: implement end_session of Logger into this method and execute for all experiment types!
    '''
    # _logger.info("waiting until saving queue is empty. %s items left." % _queue.qsize())
    _queue.join()


# Setup an aplication wide saving thread
_queue = queue.PriorityQueue()
_quit_event = threading.Event()


if alfred3.settings.experiment.type == 'qt-wk':
    _logger.info("Starting saving thread for qt-wk experiment.")
elif alfred3.settings.experiment.type == 'web':
    _logger.info("Starting global saving thread for web experiments.")

_thread = threading.Thread(target=_save_looper, name='DataSaver')
_thread.daemon = True
_thread.start()


class SavingAgentController(object):
    def __init__(self, experiment, db_cred=None):
        self._latest_data_time = None
        self._lock = threading.Lock()
        self._experiment = experiment
        self._db_cred = db_cred

        self._agents = []
        '''run agents that run in normaly'''
        self._failure_agents = []
        '''agents that run if running a normal agent fails '''

        if alfred3.settings.debugmode and alfred3.settings.debug.disable_saving:
            _logger.warning("Saving has been disabled!", self._experiment)
        else:
            self.init_saving_agents()

    def init_saving_agents(self):

        failed_to_add = False  # will be used to decide whether fall back saving agents will be used
        fallback_fail = False  # will be used to decide whether second level fall back saving agent will be added

        # add failure saving agent first
        try:
            agent = LocalSavingAgent(
                alfred3.settings.failure_local_saving_agent.name,
                alfred3.settings.failure_local_saving_agent.path,
                alfred3.settings.failure_local_saving_agent.level,
                self._experiment
            )
            self.add_failure_saving_agent(agent)
        except Exception as e:
            _logger.critical("Critical initialization abort! Adding failure SavingAgent failed with error '%s'" % e, self._experiment)
            raise SavingAgentException("Critical initialization abort! Error while adding failure SavingAgent: %s" % e)

        # add saving agents from settings
        morti = dict(self._experiment.settings.general).get("runs_on_mortimer", None)
        if morti and morti != "false" :
            try:
                host = self._db_cred["host"] + ":" + str(self._db_cred["port"])
                agent = MongoSavingAgent(
                    host,
                    self._db_cred["db"],
                    self._db_cred["collection"],
                    self._db_cred["user"],
                    self._db_cred["pw"],
                    self._db_cred["use_ssl"],
                    self._db_cred["ca_file_path"],
                    self._db_cred["activation_level"],
                    self._experiment,
                    self._db_cred["db"]
                )
                self.add_saving_agent(agent)
            except Exception as e:
                if self._experiment.settings.mongo_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing MongoSavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenter_message_manager.post_message("Initializing MongoSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        if self._experiment.settings.couchdb_saving_agent.use:
            try:
                agent = CouchDBSavingAgent(
                    self._experiment.settings.couchdb_saving_agent.url,
                    self._experiment.settings.couchdb_saving_agent.database,
                    self._experiment.settings.couchdb_saving_agent.level,
                    self._experiment
                )
                self.add_saving_agent(agent)
            except Exception as e:
                if self._experiment.settings.couchdb_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing CouchDBSavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenter_message_manager.post_message("Initializing CouchDBSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        if self._experiment.settings.mongo_saving_agent.use:
            try:
                agent = MongoSavingAgent(
                    self._experiment.settings.mongo_saving_agent.host,
                    self._experiment.settings.mongo_saving_agent.database,
                    self._experiment.settings.mongo_saving_agent.collection,
                    self._experiment.settings.mongo_saving_agent.user,
                    self._experiment.settings.mongo_saving_agent.password,
                    self._experiment.settings.mongo_saving_agent.use_ssl,
                    self._experiment.settings.mongo_saving_agent.ca_file_path,
                    self._experiment.settings.mongo_saving_agent.level,
                    self._experiment,
                    self._experiment.settings.mongo_saving_agent.auth_source
                )
                self.add_saving_agent(agent)
            except Exception as e:
                if self._experiment.settings.mongo_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing MongoSavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenter_message_manager.post_message("Initializing MongoSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        if self._experiment.settings.local_saving_agent.use:
            try:
                agent = LocalSavingAgent(
                    self._experiment.settings.local_saving_agent.name,
                    self._experiment.settings.local_saving_agent.path,
                    self._experiment.settings.local_saving_agent.level,
                    self._experiment
                )
                self.add_saving_agent(agent)
            except Exception as e:
                if self._experiment.settings.local_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing local SavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing local SavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing local SavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenter_message_manager.post_message("Initializing local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        # Falback Agents #

        if failed_to_add:

            if self._experiment.settings.fallback_couchdb_saving_agent.use:
                try:
                    agent = CouchDBSavingAgent(
                        self._experiment.settings.fallback_couchdb_saving_agent.url,
                        self._experiment.settings.fallback_couchdb_saving_agent.database,
                        self._experiment.settings.fallback_couchdb_saving_agent.level,
                        self._experiment
                    )
                    self.add_saving_agent(agent)
                    self._experiment.experimenter_message_manager.post_message("Adding fallback CouchDBSavingAgent succeeded!", "Fallback working!", self._experiment.message_manager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_couchdb_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback CouchDBSavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenter_message_manager.post_message("Initializing fallback CouchDBSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

            if self._experiment.settings.fallback_mongo_saving_agent.use:
                try:
                    agent = MongoSavingAgent(
                        self._experiment.settings.fallback_mongo_saving_agent.host,
                        self._experiment.settings.fallback_mongo_saving_agent.database,
                        self._experiment.settings.fallback_mongo_saving_agent.collection,
                        self._experiment.settings.fallback_mongo_saving_agent.user,
                        self._experiment.settings.fallback_mongo_saving_agent.password,
                        self._experiment.settings.fallback_mongo_saving_agent.level,
                        self._experiment
                    )
                    self.add_saving_agent(agent)
                    self._experiment.experimenter_message_manager.post_message("Adding fallback MongoSavingAgent succeeded!", "Fallback working!", self._experiment.message_manager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_mongo_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback MongoSavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback MongoSavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback MongoSavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenter_message_manager.post_message("Initializing fallback MongoSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

            if self._experiment.settings.fallback_local_saving_agent.use:
                try:
                    agent = LocalSavingAgent(
                        self._experiment.settings.fallback_local_saving_agent.name,
                        self._experiment.settings.fallback_local_saving_agent.path,
                        self._experiment.settings.fallback_local_saving_agent.level,
                        self._experiment
                    )
                    self.add_saving_agent(agent)
                    self._experiment.experimenter_message_manager.post_message("Adding fallback local SavingAgent succeeded!", "Fallback working!", self._experiment.message_manager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_local_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback local SavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenter_message_manager.post_message("Initializing fallback local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        # Second level fallback agent

        if fallback_fail:

            if self._experiment.settings.level2_fallback_local_saving_agent.use:
                try:
                    agent = LocalSavingAgent(
                        self._experiment.settings.level2_fallback_local_saving_agent.name,
                        self._experiment.settings.level2_fallback_local_saving_agent.path,
                        self._experiment.settings.level2_fallback_local_saving_agent.level,
                        self._experiment
                    )
                    self.add_saving_agent(agent)
                    self._experiment.experimenter_message_manager.post_message("Adding level 2 fallback local SavingAgent succeeded!", "Level 2 fallback working!", self._experiment.message_manager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.level2_fallback_local_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing level 2 fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing level 2 fallback local SavingAgent: %s" % e)
                    else:
                        _logger.warning("Initializing level 2 fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenter_message_manager.post_message("Initializing level 2 fallback local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.message_manager.WARNING)

        if self._agents == [] and not alfred3.settings.debug.disable_saving:
            _logger.critical("Session abort! List of SavingAgents is empty, but saving is not disabled.", self._experiment)
            raise SavingAgentException("Session abort! List of SavingAgents is empty, but saving is not disabled.")

    def add_saving_agent(self, saving_agent):
        if not isinstance(saving_agent, SavingAgent):
            raise TypeError

        self._agents.append(saving_agent)
        if saving_agent.activation_level <= 1:
            _logger.info("Continuous SavingAgent %s added to experiment" % saving_agent, self._experiment)
        elif saving_agent.activation_level > 1:
            _logger.info("SavingAgent %s added to experiment" % saving_agent, self._experiment)

    def add_failure_saving_agent(self, saving_agent):
        if not isinstance(saving_agent, SavingAgent):
            raise TypeError

        self._failure_agents.append(saving_agent)

    def run_saving_agents(self, level, sync=False):

        priority = 1 if sync else 5
        e = threading.Event()                           # initialise empty threading event
        data = self._experiment.data_manager.get_data()   # dictionary of the .json data file of current session
        data['save_time'] = time.time()                 # set data["save_time"] to current time
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
                            _logger.debug("Running SavingAgent %s succeeded" % agent, self._experiment)
                        else:
                            _logger.info("Running SavingAgent %s succeeded" % agent, self._experiment)
                    except Exception as e:
                        failed = True
                        _logger.error("Running SavingAgent %s failed with error '%s'" % (agent, e), self._experiment)
            if failed:
                for agent in self._failure_agents:
                    try:
                        agent.save_data(data, 1000)
                        self._latest_data_time = data_time
                        _logger.info("Running Backup SavingAgent %s succeeded" % agent, self._experiment)
                    except Exception as e:
                        _logger.critical("Running Backup SavingAgent %s failed with error '%s'" % (agent, e), self._experiment)
        else:
            _logger.info("Data snapshot taken at %s will not be saved because a newer one (%s) was already saved." % (data_time, self._latest_data_time), self._experiment)
        self._lock.release()


class SavingAgent(with_metaclass(ABCMeta, object)):
    def __init__(self, activation_level=10, experiment=None):
        self.activation_level = activation_level

        if experiment is None:
            raise SavingAgentException("Saving Agents must be initialized with experiment instance.")

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

        filename = '%s_%s_%s.json' % (time.strftime('%Y-%m-%d_t%H%M%S'), filename, self._experiment.session_id)
        self._file = os.path.join(filepath, filename)

        if os.path.exists(self._file):
            if not os.access(self._file, os.W_OK) or not os.access(self._file, os.R_OK):
                raise RuntimeError("File '%s' must be readable and writable" % self._file)

    def _save(self, data):
        try:
            with open(self._file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return "<LocalSavingAgent [path: %s]>" % self._file


class CouchDBSavingAgent(SavingAgent):
    def __init__(self, url, database, activation_level=10, experiment=None):
        import couchdb # pylint: disable=import-error

        super(CouchDBSavingAgent, self).__init__(activation_level, experiment)

        try:
            self._server = couchdb.Server(url=url)
            self._db = self._server[database]
        except Exception as e:
            raise SavingAgentException('Type: %s' % type(e))

        self._doc_id = self._experiment.session_id
        self._doc_rev = None

    def _save(self, data):
        if self._doc_rev:
            data['_rev'] = self._doc_rev

        try:
            self._db[self._doc_id] = data
            self._doc_rev = data['_rev']
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return "<CouchDBSavingAgent [url: %s, database: %s]>" % (self._server.resource.url, self._db.name)


class MongoSavingAgent(SavingAgent):
    def __init__(self, host, database, collection, user, password, use_ssl, ca_file_path, activation_level=10, experiment=None, auth_source="admin"):
        super(MongoSavingAgent, self).__init__(activation_level, experiment)

        if use_ssl and os.path.isfile(ca_file_path):  # if self-signed ssl cert is used
            self._mc = pymongo.MongoClient(host=host, username=user, password=password,
                                           ssl=use_ssl, ssl_ca_certs=ca_file_path, authSource=auth_source)
        elif use_ssl:  # if commercial ssl certificate is used
            self._mc = pymongo.MongoClient(host=host, username=user, password=password,
                                           ssl=use_ssl, authSource=auth_source)
        else:  # if no ssl encryption is used
            self._mc = pymongo.MongoClient(host=host, username=user, password=password, authSource=auth_source)

        self._db = self._mc[database]
        # if not self._db.authenticate(user, password):
        #     raise RuntimeError("Could not authenticate with %s.%s" % (host, database))

        self._col = self._db[collection]
        self._doc_id = self._experiment.session_id

    def _save(self, data):

        try:
            data['_id'] = self._doc_id
            self._col.save(data)
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return u"<MongoSavingAgent [host: %s, database: %s.%s]>" % (
            self._mc.host, self._db.name, self._col.name)
