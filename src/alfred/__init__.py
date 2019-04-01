# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

alfred enthält die Basisklasse :py:class:`Experiment`

"""
from __future__ import absolute_import

from builtins import object
__version__ = '0.2b5'


# configure alfred logger
#
# to ensure that the logger is configured properly this must be at the top of the
# __init__.py module

from .alfredlog import init_logging
init_logging(__name__)


import time
from uuid import uuid4

from .savingAgent import SavingAgentController
from .dataManager import DataManager
from .questionController import QuestionController
from .uiController import WebUserInterfaceController, QtWebKitUserInterfaceController
from . import layout
from . import settings
from . import messages

from . import alfredlog
logger = alfredlog.getLogger(__name__)


class Experiment(object):
    '''
    **Experiment** ist die Basisklasse und somit der allgemeine Objekttyp für alle mit alfred erstellten Experimente.

    |
    '''

    def __init__(self, expType, expName, expVersion, expAuthorMail, config_string='', basepath=None, customLayout=None):
        '''
        :param str expType: Typ des Experiments.
        :param str expName: Name des Experiments.
        :param str expVersion: Version des Experiments.
        :param str expAuthorMail: E-Mail Adresse des/der Autor*in des Experiments. Für den Zugriff auf die Daten aus Mortimer sollte hier die gleiche Mail-Adresse verwendet werden, wie bei der Registrierung in Mortimer.
        :param layout customLayout: Optionaler Parameter, um das Experiment mit eigenem Custom layout zu starten

        .. note:: mindestens expType und expName müssen beim Aufruf übergeben werden!

        |

        Beschreibung:
            | Bei Aufruf von *Experiment* werden :py:class:`questionController.QuestionController`, :py:class:`dataManager.DataManager`
            | und :py:class:`savingAgent.SavingAgentController` initialisiert. Zusätzlich wird ein UserInterfaceController aus
            | :py:mod:`.uiController` aufgerufen. Welcher Controller aufgerufen wird, hängt vom deklarierten Expermiment-Typ ab.

        |


        **Momentan implementierte Typen für Experimente:**

        =========  =========================================== ===================================================
        Typ        Beschreibung                                uiController
        =========  =========================================== ===================================================
        **'qt'**   Lokales qt-Interface wird genutzt.          :py:class:`uiController.QtUserInterfaceController`
        **'web'**  Bereitstellung als HTML-Seite via Webserver :py:class:`uiController.WebUserInterfaceController`
        =========  =========================================== ===================================================

        |

        :raises ValueError: Falls Parameter falsch oder nicht übergeben werden.

        |
        |
        '''

        if type(expName) != str or expName == '' or type(expVersion) != str or expVersion == '' or not(expType == 'qt' or
                                                                                                       expType == 'web' or expType == 'qt-wk'):
            raise ValueError("expName and expVersion must be a non empty strings and expType must be 'qt' or 'web'")

        self._author_mail = expAuthorMail

        #: Name des Experiments
        self._name = expName

        #: Version des Experiments
        self._version = expVersion

        #: Typ des Experiments
        self._type = expType
        if self._type != settings.experiment.type:
            raise RuntimeError("experiment types must be equal in script and config file")

        #: Uid des Experiments
        self._uuid = uuid4().hex
        logger.info("Alfred %s experiment session initialized! Alfred version: %s, experiment name: %s, experiment version: %s" % (self._type, __version__, self._name, self._version), self)

        self._settings = settings.ExperimentSpecificSettings(config_string)
        self._messageManager = messages.MessageManager()
        self._experimenterMessageManager = messages.MessageManager()

        self._questionController = QuestionController(self)

        # Determine web layout if necessary
        if self._type == 'web' or self._type == 'qt-wk':
            if customLayout:
                web_layout = customLayout
            elif 'web_layout' in self._settings.experiment and hasattr(layout, self._settings.experiment.web_layout):
                web_layout = getattr(layout, self._settings.experiment.web_layout)()
            elif 'web_layout' in self._settings.experiment and not hasattr(layout, self._settings.experiment.web_layout):
                logger.warning("Layout specified in config.conf does not exist! Switching to BaseWebLayout", self)
                web_layout = None

        if self._type == 'web':
            self._userInterfaceController = WebUserInterfaceController(self, layout=web_layout)

        elif self._type == 'qt-wk':
            logger.warning("Experiment type qt-wk is experimental!!!", self)
            self._userInterfaceController = QtWebKitUserInterfaceController(self, fullScreen=settings.experiment.qtFullScreen, weblayout=web_layout)

        else:
            ValueError("unknown type: '%s'" % self._type)

        self._dataManager = DataManager(self)
        self._savingAgentController = SavingAgentController(self)

        self._testCondition = ''
        self._finished = False
        self._startTimeStamp = None
        self._start_time = None

        if basepath is not None:
            logger.warning("Usage of basepath is depricated.", self)

    def start(self):
        '''
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`uiController.QtUserInterfaceController.start` aufgerufen.
        '''
        self.questionController.generateUnsetTagsInSubtree()
        self._start_time = time.time()
        self._startTimeStamp = time.strftime('%Y-%m-%dT%H%M%S')
        logger.info("Experiment.start() called. Session is starting.", self)
        self._userInterfaceController.start()

    def finish(self):
        '''
        Beendet das Experiment. Ruft  :meth:`questionController.QuestionController.changeToFinishedGroup` auf und setzt **self._finished** auf *True*.

        '''
        if self._finished:
            logger.warning("Experiment.finish() called. Experiment was already finished. Leave Method")
            return
        logger.info("Experiment.finish() called. Session is finishing.", self)
        self._finished = True
        self._questionController.changeToFinishedGroup()

        # run savingAgentController
        self._savingAgentController.runSavingAgents(99)

    @property
    def author_mail(self):
        '''
        Achtung: *read-only*

        :return: E-Mail des/der Autor*in **author_mail** (*str*)
        '''
        return self._author_mail

    @property
    def type(self):
        '''
        Achtung: *read-only*

        :return: Experimenttyp **expType** (*str*)
        '''

        return self._type

    @property
    def version(self):
        '''
        Achtung: *read-only*

        :return: Experimentversion **expVersion** (*str*)
        '''
        return self._version

    @property
    def name(self):
        '''
        Achtung: *read-only*

        :return: Experimentname **expName** (*str*)
        '''
        return self._name

    @property
    def startTimeStamp(self):
        return self._startTimeStamp

    @property
    def messageManager(self):
        return self._messageManager

    @property
    def experimenterMessageManager(self):
        return self._experimenterMessageManager

    @property
    def uuid(self):
        return self._uuid

    @property
    def userInterfaceController(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`uiController.QtUserInterfaceController` oder :py:class:`uiController.WebUserInterfaceController`
        '''
        return self._userInterfaceController

    @property
    def questionController(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`questionController.QuestionController`
        '''
        return self._questionController

    @property
    def dataManager(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`dataManager.DataManager`
        '''
        return self._dataManager

    @property
    def savingAgentController(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`savingAgent.SavingAgentController`
        '''
        return self._savingAgentController

    @property
    def settings(self):
        return self._settings

    @property
    def finished(self):
        '''
        Achtung: *read-only*

        :return: Experiment beendet? **self._finished** (*bool*)
        '''
        return self._finished

    @property
    def testCondition(self):
        '''
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        '''
        return self._testCondition

    def addTestCondition(self, s):
        self._testCondition = self._testCondition + '.' + s if self._testCondition else s
