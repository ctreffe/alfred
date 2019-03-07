# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

"""
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import object
from abc import ABCMeta, abstractmethod


import json
import time
import os
import queue
import threading

import pymongo

import alfred.settings
from .exceptions import SavingAgentRunException, SavingAgentException

from . import alfredlog
from future.utils import with_metaclass
_logger = alfredlog.getLogger(__name__)


def _save_worker():
    try:
        while True:
            try:
                (i, event, data, data_time, level, sac) = _queue.get_nowait()
            except queue.Empty:
                break
            sac._do_saving(data, data_time, level)
            event.set()
            _queue.task_done()
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.critical("MOST OUTER EXCEPTION IN SAVE WORKER!!!")


def _save_looper(sleeptime=1):
    while not _quit_event.is_set():
        _save_worker()
        time.sleep(sleeptime)


def wait_for_saving_thread():
    '''
    .. todo:: implement endSession of Logger into this method and execute for all experiment types!
    '''
    # _logger.info("waiting until saving queue is empty. %s items left." % _queue.qsize())
    _queue.join()


# Setup an aplication wide saving thread
_queue = queue.PriorityQueue()
_quit_event = threading.Event()


if alfred.settings.experiment.type == 'qt-wk':
    _logger.info("Starting saving thread for qt-wk experiment.")
    _thread = threading.Thread(target=_save_looper, name='DataSaver')
    _thread.daemon = True
    _thread.start()
elif alfred.settings.experiment.type == 'web':
    _logger.info("Starting global saving thread for web experiments.")
    _thread = threading.Thread(target=_save_looper, name='DataSaver')
    _thread.daemon = True
    _thread.start()


class SavingAgentController(object):
    def __init__(self, experiment):
        self._latest_data_time = None
        self._lock = threading.Lock()
        self._experiment = experiment

        self._agents = []
        '''run agents that run in normaly'''
        self._failure_agents = []
        '''agents that run if running a normal agent fails '''

        if alfred.settings.debugmode and alfred.settings.debug.disable_saving:
            _logger.warning("Saving has been disabled!", self._experiment)
        else:
            self.initSavingAgents()

    def initSavingAgents(self):

        failed_to_add = False  # will be used to decide whether fall back saving agents will be used
        fallback_fail = False  # will be used to decide whether second level fall back saving agent will be added

        # add failure saving agent first
        try:
            agent = LocalSavingAgent(
                alfred.settings.failure_local_saving_agent.name,
                alfred.settings.failure_local_saving_agent.path,
                alfred.settings.failure_local_saving_agent.level,
                self._experiment
            )
            self.addFailureSavingAgent(agent)
        except Exception as e:
            _logger.critical("Critical initialization abort! Adding failure SavingAgent failed with error '%s'" % e, self._experiment)
            raise SavingAgentException("Critical initialization abort! Error while adding failure SavingAgent: %s" % e)

        # add saving agents from settings

        if self._experiment.settings.couchdb_saving_agent.use:
            try:
                agent = CouchDBSavingAgent(
                    self._experiment.settings.couchdb_saving_agent.url,
                    self._experiment.settings.couchdb_saving_agent.database,
                    self._experiment.settings.couchdb_saving_agent.level,
                    self._experiment
                )
                self.addSavingAgent(agent)
            except Exception as e:
                if self._experiment.settings.couchdb_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing CouchDBSavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenterMessageManager.postMessage("Initializing CouchDBSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

        if self._experiment.settings.mongo_saving_agent.use:
            try:
                agent = MongoSavingAgent(
                    self._experiment.settings.mongo_saving_agent.host,
                    self._experiment.settings.mongo_saving_agent.database,
                    self._experiment.settings.mongo_saving_agent.collection,
                    self._experiment.settings.mongo_saving_agent.user,
                    self._experiment.settings.mongo_saving_agent.password,
                    self._experiment.settings.mongo_saving_agent.use_ssl,
                    self._experiment.settings.mongo_saving_agent.level,
                    self._experiment
                )
                self.addSavingAgent(agent)
            except Exception as e:
                if self._experiment.settings.mongo_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing MongoSavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing MongoSavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenterMessageManager.postMessage("Initializing MongoSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

        if self._experiment.settings.local_saving_agent.use:
            try:
                agent = LocalSavingAgent(
                    self._experiment.settings.local_saving_agent.name,
                    self._experiment.settings.local_saving_agent.path,
                    self._experiment.settings.local_saving_agent.level,
                    self._experiment
                )
                self.addSavingAgent(agent)
            except Exception as e:
                if self._experiment.settings.local_saving_agent.assure_initialization:
                    _logger.critical("Assured initialization abort! Initializing local SavingAgent failed with error '%s'" % e, self._experiment)
                    raise SavingAgentException("Assured initialization abort! Error while initializing local SavingAgent: %s" % e)
                else:
                    failed_to_add = True
                    _logger.warning("Initializing local SavingAgent failed with error '%s'" % e, self._experiment)
                    self._experiment.experimenterMessageManager.postMessage("Initializing local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

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
                    self.addSavingAgent(agent)
                    self._experiment.experimenterMessageManager.postMessage("Adding fallback CouchDBSavingAgent succeeded!", "Fallback working!", self._experiment.messageManager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_couchdb_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback CouchDBSavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback CouchDBSavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenterMessageManager.postMessage("Initializing fallback CouchDBSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

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
                    self.addSavingAgent(agent)
                    self._experiment.experimenterMessageManager.postMessage("Adding fallback MongoSavingAgent succeeded!", "Fallback working!", self._experiment.messageManager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_mongo_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback MongoSavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback MongoSavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback MongoSavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenterMessageManager.postMessage("Initializing fallback MongoSavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

            if self._experiment.settings.fallback_local_saving_agent.use:
                try:
                    agent = LocalSavingAgent(
                        self._experiment.settings.fallback_local_saving_agent.name,
                        self._experiment.settings.fallback_local_saving_agent.path,
                        self._experiment.settings.fallback_local_saving_agent.level,
                        self._experiment
                    )
                    self.addSavingAgent(agent)
                    self._experiment.experimenterMessageManager.postMessage("Adding fallback local SavingAgent succeeded!", "Fallback working!", self._experiment.messageManager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.fallback_local_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing fallback local SavingAgent: %s" % e)
                    else:
                        fallback_fail = True
                        _logger.warning("Initializing fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenterMessageManager.postMessage("Initializing fallback local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

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
                    self.addSavingAgent(agent)
                    self._experiment.experimenterMessageManager.postMessage("Adding level 2 fallback local SavingAgent succeeded!", "Level 2 fallback working!", self._experiment.messageManager.SUCCESS)
                except Exception as e:
                    if self._experiment.settings.level2_fallback_local_saving_agent.assure_initialization:
                        _logger.critical("Assured initialization abort! Initializing level 2 fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        raise SavingAgentException("Assured initialization abort! Error while initializing level 2 fallback local SavingAgent: %s" % e)
                    else:
                        _logger.warning("Initializing level 2 fallback local SavingAgent failed with error '%s'" % e, self._experiment)
                        self._experiment.experimenterMessageManager.postMessage("Initializing level 2 fallback local SavingAgent failed. Do <b>NOT</b> continue if this saving agent is critical to your experiment!", "SavingAgent warning!", self._experiment.messageManager.WARNING)

        if self._agents == [] and not alfred.settings.debug.disable_saving:
            _logger.critical("Session abort! List of SavingAgents is empty, but saving is not disabled.", self._experiment)
            raise SavingAgentException("Session abort! List of SavingAgents is empty, but saving is not disabled.")

    def addSavingAgent(self, savingAgent):
        if not isinstance(savingAgent, SavingAgent):
            raise TypeError

        self._agents.append(savingAgent)
        if savingAgent.activation_level <= 1:
            _logger.info("Continuous SavingAgent %s added to experiment" % savingAgent, self._experiment)
        elif savingAgent.activation_level > 1:
            _logger.info("SavingAgent %s added to experiment" % savingAgent, self._experiment)

    def addFailureSavingAgent(self, savingAgent):
        if not isinstance(savingAgent, SavingAgent):
            raise TypeError

        self._failure_agents.append(savingAgent)

    def runSavingAgents(self, level, sync=False):

        priority = 1 if sync else 5
        e = threading.Event()                           # initialise empty threading event
        data = self._experiment.dataManager.getData()   # dictionary of the .json data file of current session
        data['save_time'] = time.time()                 # set data["save_time"] to current time
        _queue.put((priority, e, data, time.time(), level, self))
        if sync:
            e.wait()

    def _do_saving(self, data, data_time, level):
        self._lock.acquire()
        if self._latest_data_time is None or self._latest_data_time < data_time:
            failed = False
            for agent in self._agents:
                if agent.activation_level <= level:
                    try:
                        agent.saveData(data, level)
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
                        agent.saveData(data, 1000)
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

    def saveData(self, data, level):

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

        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        if not os.path.isdir(filepath):
            raise RuntimeError("save path '%s' must be an directory" % filepath)
        if not os.access(filepath, os.W_OK):
            raise RuntimeError("save path '%s' must be writable" % filepath)

        filename = '%s_%s_%s.json' % (time.strftime('%Y-%m-%dT%H%M%S'), filename, self._experiment.uuid)
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
        import couchdb

        super(CouchDBSavingAgent, self).__init__(activation_level, experiment)

        try:
            self._server = couchdb.Server(url=url)
            self._db = self._server[database]
        except Exception as e:
            raise SavingAgentException('Type: %s' % type(e))

        self._doc_id = self._experiment.uuid
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
    def __init__(self, host, database, collection, user, password, use_ssl, activation_level=10, experiment=None):
        super(MongoSavingAgent, self).__init__(activation_level, experiment)

        self._mc = pymongo.MongoClient(host, ssl=use_ssl)
        self._db = self._mc[database]
        # if not self._db.authenticate(user, password):
        #     raise RuntimeError("Could not authenticate with %s.%s" % (host, database))

        self._col = self._db[collection]

        self._doc_id = self._experiment.uuid

    def _save(self, data):

        try:
            data['_id'] = self._doc_id
            self._col.save(data)
        except Exception as e:
            raise SavingAgentRunException("Error while saving: %s" % e)

    def __str__(self):
        return u"<MongoSavingAgent [host: %s, database: %s.%s]>" % (
            self._mc.host, self._db.name, self._col.name)
