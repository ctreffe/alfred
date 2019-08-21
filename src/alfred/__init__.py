# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

alfred enthält die Basisklasse :py:class:`Experiment`

"""
from __future__ import absolute_import

from builtins import object
__version__ = '0.3b1'


# configure alfred logger
#
# to ensure that the logger is configured properly this must be at the top of the
# __init__.py module

from .alfredlog import init_logging
init_logging(__name__)


import time
from uuid import uuid4

from .saving_agent import SavingAgentController
from .data_manager import DataManager
from .page_controller import PageController
from .ui_controller import WebUserInterfaceController, QtWebKitUserInterfaceController
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

    def __init__(self, type=None, title=None, version=None, author=None, config_string='', basepath=None, custom_layout=None):
        '''
        :param str type: Experiment type.
        :param str title: Experiment title.
        :param str version: Experiment version.
        :param str author: Experiment author. If a local experiment saves data to mortimer, this should be the mortimer username.
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
        '''

        # get experiment metadata
        # the if-else clauses ensure backwards compatibility, if users defined the metadata in script.py
        self._author = author if author else settings.experiment.author
        self._title = title if title else settings.experiment.title
        self._version = version if version else settings.experiment.version
        self._type = type if type else settings.experiment.type

        # FOR BACKWARDS COMPATIBILITY
        # raise errors if user defined metadata in script.py that doesn't match the data given in config.conf
        if self._title != settings.experiment.title:
            raise RuntimeError("Experiment titles must be equal in script and config file.")
        if self._author != settings.experiment.author:
            raise RuntimeError("Experiment authors must be equal in script and config file.")
        if self._version != settings.experiment.version:
            raise RuntimeError("Experiment versions must be equal in script and config file")
        if self._type != settings.experiment.type:
            raise RuntimeError("Experiment types must be equal in script and config file.")

        #: Uid des Experiments
        self._uuid = uuid4().hex
        logger.info("Alfred %s experiment session initialized! Alfred version: %s, experiment name: %s, experiment version: %s" % (self._type, __version__, self._title, self._version), self)

        self._settings = settings.ExperimentSpecificSettings(config_string)
        self._message_manager = messages.MessageManager()
        self._experimenter_message_manager = messages.MessageManager()

        self._page_controller = PageController(self)

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
            self._user_interface_controller = WebUserInterfaceController(self, layout=web_layout)

        elif self._type == 'qt-wk':
            logger.warning("Experiment type qt-wk is experimental!!!", self)
            self._user_interface_controller = QtWebKitUserInterfaceController(self, full_scren=settings.experiment.qt_full_screen, weblayout=web_layout)

        else:
            ValueError("unknown type: '%s'" % self._type)

        self._data_manager = DataManager(self)
        self._saving_agent_controller = SavingAgentController(self)

        self._condition = ''
        self._session = ''
        self._finished = False
        self._start_timestamp = None
        self._start_time = None

        if basepath is not None:
            logger.warning("Usage of basepath is depricated.", self)

    def update(self, title, version, author, type="web"):
        self._title = title
        self._version = version
        self._author = author
        self._type = type

    def start(self):
        '''
        Startet das Experiment, wenn die Bereitstellung lokal erfolgt.

        Für Qt-Experimente wird :meth:`ui_controller.QtUserInterfaceController.start` aufgerufen.
        '''
        self.page_controller.generate_unset_tags_in_subtree()
        self._start_time = time.time()
        self._start_timestamp = time.strftime('%Y-%m-%d_t%H%M%S')
        logger.info("Experiment.start() called. Session is starting.", self)
        self._user_interface_controller.start()

    def finish(self):
        '''
        Beendet das Experiment. Ruft  :meth:`page_controller.PageController.change_to_finished_group` auf und setzt **self._finished** auf *True*.

        '''
        if self._finished:
            logger.warning("Experiment.finish() called. Experiment was already finished. Leave Method")
            return
        logger.info("Experiment.finish() called. Session is finishing.", self)
        self._finished = True
        self._page_controller.change_to_finished_group()

        # run saving_agent_controller
        self._saving_agent_controller.run_saving_agents(99)

    @property
    def author(self):
        '''
        Achtung: *read-only*

        :return: Experiment author **author** (*str*)
        '''
        return self._author

    @property
    def type(self):
        '''
        Achtung: *read-only*

        :return: Type of experiment **type** (*str*)
        '''

        return self._type

    @property
    def version(self):
        '''
        Achtung: *read-only*

        :return: Experiment version **version** (*str*)
        '''
        return self._version

    @property
    def title(self):
        '''
        Achtung: *read-only*

        :return: Experiment title **title** (*str*)
        '''
        return self._title

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def message_manager(self):
        return self._message_manager

    @property
    def experimenter_message_manager(self):
        return self._experimenter_message_manager

    @property
    def uuid(self):
        return self._uuid

    @property
    def user_interface_controller(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`ui_controller.QtUserInterfaceController` oder :py:class:`ui_controller.WebUserInterfaceController`
        '''
        return self._user_interface_controller

    @property
    def page_controller(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`page_controller.PageController`
        '''
        return self._page_controller

    @property
    def data_manager(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`data_manager.DataManager`
        '''
        return self._data_manager

    @property
    def saving_agent_controller(self):
        '''
        Achtung: *read-only*

        :return: :py:class:`saving_agent.SavingAgentController`
        '''
        return self._saving_agent_controller

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
    def condition(self):
        '''
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        '''
        return self._condition

    def add_condition(self, s):
        self._condition = self._condition + '.' + s if self._condition else s

    @property
    def session(self):
        '''
        *read-only*

        :return: Current TestCondition (*str or unicode*)
        '''
        return self._session

    def add_session(self, s):
        self._session = self._session + '.' + s if self._session else s
