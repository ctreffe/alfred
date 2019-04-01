# -*- coding: utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

Das Modul *ui_controller* stellt die Klassen zur Verfügung, die die Darstellung und die Steuerelemente auf verschiedenen Interfaces verwalten.
'''
from __future__ import absolute_import


from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
from abc import ABCMeta, abstractmethod
from uuid import uuid4
from io import StringIO
import threading

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
import PySide2.QtCore as QtCore
from PySide2.QtWebEngineWidgets import QWebEngineView as QWebView

from ._core import Direction
from .layout import BaseWebLayout

import alfred.settings
from .helpmates import localserver as localserver
from future.utils import with_metaclass


class UserInterfaceController(with_metaclass(ABCMeta, object)):
    '''
    Abstrakte Basisklasse, die die Grundfunktionalität für alle UserIntferaces bereitstellt

    '''

    def __init__(self, experiment, layout=None):
        '''
        :param experiment: Ein Objekt vom Typ Experiment
        :param layout: Ein Objekt vom Typ Layout (None bedeutet Standardlayout)

        |

        Bei Aufruf der Klasse wird mittels :meth:`.change_layout` ein :attr:`.layout` gesetzt.

        '''
        self._experiment = experiment
        self._layout = None
        self._oldQuestion = None

        if layout is None:
            self.change_layout(BaseQtLayout() if experiment.type == 'qt' else BaseWebLayout())
        else:
            self.change_layout(layout)

    @abstractmethod
    def render(self):
        pass

    @property
    def layout(self):
        return self._get_layout()

    def _get_layout(self):
        return self._layout

    def change_layout(self, layout):
        if self._layout is not None:
            self._layout.deactivate()
        self._layout = layout
        self._layout.activate(self._experiment, self)

    def move_forward(self):
        if self._experiment.question_controller.allow_leaving(Direction.FORWARD):
            self._experiment.question_controller.current_question._on_hiding_widget()
            if self._experiment.question_controller.can_move_forward:
                self._experiment.question_controller.move_forward()
                self._experiment.saving_agent_controller.run_saving_agents(1)
            else:
                self._experiment.finish()
            self._experiment.question_controller.current_question._on_showing_widget()

    def move_backward(self):
        if self._experiment.question_controller.allow_leaving(Direction.BACKWARD):
            self._experiment.question_controller.current_question._on_hiding_widget()
            self._experiment.question_controller.move_backward()
            self._experiment.saving_agent_controller.run_saving_agents(1)
            self._experiment.question_controller.current_question._on_showing_widget()

    def move_to_position(self, posList):
        if self._experiment.question_controller.allow_leaving(Direction.JUMP):
            self._experiment.question_controller.current_question._on_hiding_widget()
            self._experiment.question_controller.move_to_position(posList)
            self._experiment.saving_agent_controller.run_saving_agents(1)
            self._experiment.question_controller.current_question._on_showing_widget()

    def start(self):
        self._experiment.question_controller.enter()
        self._experiment.question_controller.current_question._on_showing_widget()


class WebUserInterfaceController(UserInterfaceController):
    def __init__(self, experiment, layout=None):

        self._callablesDict = {}
        self._dynamicFilesDict = {}
        self._staticFilesDict = {}
        self._basepath = alfred.settings.webserver.basepath

        super(WebUserInterfaceController, self).__init__(experiment, layout)

    @property
    def basepath(self):
        return self._basepath

    def render(self):
        self._experiment.question_controller.current_question.prepare_web_widget()

        jsScripts = []
        js_urls = []
        cssScripts = []
        css_urls = []

        # update with layout
        jsScripts = jsScripts + self._layout.javascript_code
        js_urls = js_urls + self._layout.javascript_urls
        cssScripts = cssScripts + self._layout.css_code
        css_urls = css_urls + self._layout.css_urls

        # update with current_question
        jsScripts = jsScripts + self._experiment.question_controller.current_question.js_code
        js_urls = js_urls + self._experiment.question_controller.current_question.js_urls
        cssScripts = cssScripts + self._experiment.question_controller.current_question.css_code
        css_urls = css_urls + self._experiment.question_controller.current_question.css_urls

        # sort lists by first item
        jsScripts.sort(key=lambda x: x[0])
        js_urls.sort(key=lambda x: x[0])
        cssScripts.sort(key=lambda x: x[0])
        css_urls.sort(key=lambda x: x[0])

        # build html code
        html = "<!DOCTYPE html>\n<html><head><title>ALFRED</title>"

        for i, jsURL in js_urls:
            html = html + "<script type=\"text/javascript\" src=\"%s\"></script>" % jsURL

        for i, jsScript in jsScripts:
            html = html + "<script type=\"text/javascript\">%s</script>" % jsScript

        for i, cssURL in css_urls:
            html = html + "<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\" />" % cssURL

        for i, cssScript in cssScripts:
            html = html + "<style type=\"text/css\">%s</style>" % cssScript

        html = html + "</head><body><form id=\"form\" method=\"post\" action=\"%s/experiment\" autocomplete=\"off\" accept-charset=\"UTF-8\">" % self._basepath

        html = html + self._layout.render()

        html = html + "</form></body></html>"

        return html

    def render_html(self):
        return self.render()

    def get_dynamic_file(self, identifier):
        fileObj, content_type = self._dynamicFilesDict[identifier]
        fileObj.seek(0)
        strIO = StringIO(fileObj.read())
        strIO.seek(0)
        return strIO, content_type

    def add_dynamic_file(self, file_obj, content_type=None):
        identifier = uuid4().hex
        while identifier in self._dynamicFilesDict:
            identifier = uuid4().hex

        self._dynamicFilesDict[identifier] = (file_obj, content_type)
        return self._basepath + '/dynamicfile/' + identifier

    def get_static_file(self, identifier):
        return self._staticFilesDict[identifier]

    def add_static_file(self, path, content_type=None):
        if not os.path.isabs(path):
            path = os.path.join(alfred.settings.general.external_files_dir, path)
        identifier = uuid4().hex
        if alfred.settings.debugmode:
            if not hasattr(self, 'sf_counter'):
                self.sf_counter = 0
            self.sf_counter += 1
            identifier = str(self.sf_counter)
        while identifier in self._staticFilesDict:
            identifier = uuid4().hex
        self._staticFilesDict[identifier] = (path, content_type)
        return self._basepath + '/staticfile/' + identifier

    def get_callable(self, identifier):
        return self._callablesDict[identifier]

    def add_callable(self, f):
        identifier = uuid4().hex
        while identifier in self._callablesDict:
            identifier = uuid4().hex

        self._callablesDict[identifier] = f
        return self._basepath + '/callable/' + identifier

    def update_with_user_input(self, d):
        self._experiment.question_controller.current_question.set_data(d)

    def jump_url_from_pos_list(self, posList):
        return self._basepath + '/experiment?move=jump&par=' + '.'.join(posList)


try:
    class ThreadHelper(QtCore.QObject):
        renderSignal = QtCore.Signal()

        def __init__(self, ui_controller):
            super(ThreadHelper, self).__init__()
            self._uiController = ui_controller
            self.renderSignal.connect(self.render_slot)

        def render(self):
            self.renderSignal.emit()

        @QtCore.Slot()
        def render_slot(self):
            self._uiController.render_slot()
except NameError:
    from .alfredlog import getLogger
    logger = getLogger((__name__))
    logger.warning("Can't create ThreadHelper. (Needed for Qt)")


class QtWebKitUserInterfaceController(WebUserInterfaceController):
    def __init__(self, experiment, weblayout=None, qtlayout=None, fullScreen=True, **kwargs):

        self._helper = ThreadHelper(self)

        localserver.set_experiment(experiment)

        # initialize qt
        self._app = QApplication([])
        self._qtWindow = QMainWindow()
        self._qtWindow.setMinimumHeight(720)
        self._qtWindow.setMinimumWidth(1024)
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self._webView = QWebView()
        # self._qtMainScrollArea = QScrollArea()
        # self._qtMainScrollArea.setWidgetResizable(True)  # Must be set to True in order for layout to work properly
        # self._qtMainScrollArea.setStyleSheet("QScrollArea {background: white; border: none}")

        layout.addWidget(self._webView)

        self._qtWindow.setCentralWidget(widget)

        self._current_main_widget = None
        # self._qtlayout = None

        self._fullscreen = fullScreen

        super(QtWebKitUserInterfaceController, self).__init__(experiment, weblayout)
        # self.changeQtLayout(qtlayout or BaseQtLayout())

    def _get_layout(self):
        return self._layout

    def render_html(self):

        return super(QtWebKitUserInterfaceController, self).render()

    def render(self):
        self._helper.render()

    def render_slot(self):

            # self._qtMainScrollArea.hide()
        self._webView.show()
        # TODO: Check if this fix is ok!
        # self._webView.load('http://127.0.0.1:5000/experiment')#http://127.0.0.1:5000/experiment

    def move_forward(self):

        super(QtWebKitUserInterfaceController, self).move_forward()

        self.render()

    def move_backward(self):

        super(QtWebKitUserInterfaceController, self).move_backward()

        self.render()

    def move_to_position(self, posList):

        super(QtWebKitUserInterfaceController, self).move_forward()
        self.render()

    def start(self):
        super(QtWebKitUserInterfaceController, self).start()
        # startup flask
        t = threading.Thread(target=localserver.app.run, name="Flask Thread")
        t.daemon = True
        t.start()
        import time
        time.sleep(2)  # TODO: What is this?
        self._webView.setUrl("http://127.0.0.1:5000/experiment")

        if self._fullscreen:
            self._qtWindow.showFullScreen()
        else:
            self._qtWindow.show()

        self.render()
        self._app.exec_()

        # after leaving app this code will be executed
        from .saving_agent import wait_for_saving_thread
        wait_for_saving_thread()
