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
from .data_manager import DataManager
from .question_controller import QuestionController
from .ui_controller import WebUserInterfaceController, QtWebKitUserInterfaceController
from . import layout
from . import settings
from . import messages

from . import alfredlog
logger = alfredlog.get_logger(__name__)


class Experiment(object):
    '''
    **Experiment** ist die Basisklasse und somit der allgemeine Objekttyp für alle mit alfred erstellten Experimente.

    |
    '''

    def __init__(self, exp_type, exp_name, exp_version, exp_author_mail, config_string='', basepath=None, custom_layout=None):
        '''
        :param str exp_type: Typ des Experiments.
        :param str exp_name: Name des Experiments.
        :param str exp_version: Version des Experiments.
        :param str exp_author_mail: E-Mail Adresse des/der Autor*in des Experiments. Für den Zugriff auf die Daten aus Mortimer sollte hier die gleiche Mail-Adresse verwendet werden, wie bei der Registrierung in Mortimer.
        :param layout custom_layout: Optionaler Parameter, um das Experiment mit eigenem Custom layout zu starten

        .. note:: mindestens exp_type und exp_name müssen beim Aufruf übergeben werden!

        |

        Beschreibung:
            | Bei Aufruf von *Experiment* werden :py:class:`question_controller.QuestionController`, :py:class:`data_manager.DataManager`
            | und :py:class:`savingAgent.SavingAgentController` initialisiert. Zusätzlich wird ein UserInterfaceController aus
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
        '''

        if type(exp_name) != str or exp_name == '' or type(exp_version) != str or exp_version == '' or not(exp_type == 'qt' or
                                                                                                       exp_type == 'web' or exp_type == 'qt-wk'):
            raise ValueError("exp_name and exp_version must be a non empty strings and exp_type must be 'qt' or 'web'")

        self._author_mail = exp_author_mail

        #: Name des Experiments
        self._name = exp_name

        #: Version des Experiments
        self._version = exp_version

        #: Typ des Experiments
        self._type = exp_type
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
            if custom_layout:
                web_layout = custom_layout
            elif 'web_layout' in self._settings.experiment and hasattr(layout, self._settings.experiment.web_layout):
                web_layout = getattr(layout, self._settings.experiment.web_layout)()
            elif 'web_layout' in self._settings.experiment and not hasattr(layout, self._settings.experiment.web_layout):
                logger.warning("Layout specified in config.conf does not exist! Switching to BaseWebLayout", self)
                web_layout = None

        if self._type == 'web':
            self._userInterfaceController = WebUserInterfaceController(self, layout=web_layout)

        elif self._type == 'qt-wk':
            logger.warning("Experiment type qt-wk is experimental!!!", self)
            self._userInterfaceController = QtWebKitUserInterfaceController(self, full_scren=settings.experiment.qtFullScreen, weblayout=web_layout)

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

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        '''
        self.question_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._startTimeStamp = time.strftime('%Y-%m-%dT%H%M%S')
        logger.info("Experiment.start() called. Session is starting.", self)
        self._userInterfaceController.start()

    def finish(self):
        '''
        Beendet das Experiment. Ruft  :meth:`question_controller.QuestionController.change_to_finished_group` auf und setzt **self._finished** auf *True*.

        '''
        if self._finished:
            logger.warning("Experiment.finish() called. Experiment was already finished. Leave Method")
            return
        logger.info("Experiment.finish() called. Session is finishing.", self)
        self._finished = True
        self._questionController.change_to_finished_group()

        # run saving_agent_controller
        self._savingAgentController.run_saving_agents(99)

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

        :return: Experimenttyp **exp_type** (*str*)
        '''

        return self._type

    @property
    def version(self):
        '''
        Achtung: *read-only*

        :return: Experimentversion **exp_version** (*str*)
        '''
        return self._version

    @property
    def name(self):
        '''
        Achtung: *read-only*

        :return: Experimentname **exp_name** (*str*)
        '''
        return self._name

    @property
    def start_timestamp(self):
        return self._startTimeStamp

    @property
    def message_manager(self):
        return self._messageManager

    @property
    def experimenter_message_manager(self):
        return self._experimenterMessageManager

    @property
    def uuid(self):
        return self._uuid

    @property
    def user_interface_controller(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`ui_controller.QtUserInterfaceController` oder :py:class:`ui_controller.WebUserInterfaceController`
        '''
        return self._userInterfaceController

    @property
    def question_controller(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`question_controller.QuestionController`
        '''
        return self._questionController

    @property
    def data_manager(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`data_manager.DataManager`
        '''
        return self._dataManager

    @property
    def saving_agent_controller(self):
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
    def test_condition(self):
        '''
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        '''
        return self._testCondition

    def add_test_condition(self, s):
        self._testCondition = self._testCondition + '.' + s if self._testCondition else s
