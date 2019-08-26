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
import webbrowser
from uuid import uuid4

from .saving_agent import SavingAgentController
from .data_manager import DataManager
from .page_controller import PageController
from .ui_controller import WebUserInterfaceController, QtWebKitUserInterfaceController
from .helpmates import socket_checker
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

    def __init__(self, exp_type=None, exp_name=None, exp_version=None, config_string='', basepath=None, custom_layout=None):
        '''
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

        if exp_type or exp_name or exp_version:
            raise SyntaxError("The definition of experiment title, type, or version in script.py is deprecated. Please define these parameters in config.conf. In your script.py, just use 'exp = Experiment()'.")

        # get experiment metadata
        self._author = settings.experiment.author
        self._title = settings.experiment.title
        self._version = settings.experiment.version
        self._type = settings.experiment.type

        # Uids for experiment (when hosted by mortimer) and session
        self._mortimer_id = '(Local experiment without Mortimer ID)'
        self._session_id = uuid4().hex

        # Experiment startup message
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

    def update(self, title, version, author, uuid, type="web"):
        self._title = title
        self._version = version
        self._author = author
        self._type = type
        self._uuid = uuid

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

    def append(self, *items):
        for item in items:
            self.page_controller.append(item)

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
    def mortimer_id(self):
        return self._mortimer_id

    @property
    def session_id(self):
        return self._session_id

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


class Generator(object):
    def generate_experiment(self):
        pass


def run(generator, open=True, window=1):
    if settings.experiment.type == "qt-wk":
        gen = Generator()
        gen.generate_experiment = generator.__get__(gen, Generator)
        exp = gen.generate_experiment()
        exp.start()
    elif settings.experiment.type == "web":
        import sys
        import alfred.helpmates.localserver as ls
        ls.set_generator(generator)
        port = 5000
        while not socket_checker(port):
            port += 1
        if open:
            webbrowser.open('http://127.0.0.1:{port}/start'.format(port=port), new=window)
        sys.stderr.writelines([" * Start local experiment using http://127.0.0.1:%d/start\n" % port])
        ls.app.run(port=port, threaded=True)
    else:
        RuntimeError("Unexpected value of experiment type")
