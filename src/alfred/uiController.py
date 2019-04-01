# -*- coding: utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

Das Modul *uiController* stellt die Klassen zur Verfügung, die die Darstellung und die Steuerelemente auf verschiedenen Interfaces verwalten.
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

        Bei Aufruf der Klasse wird mittels :meth:`.changeLayout` ein :attr:`.layout` gesetzt.

        '''
        self._experiment = experiment
        self._layout = None
        self._oldQuestion = None

        if layout is None:
            self.changeLayout(BaseQtLayout() if experiment.type == 'qt' else BaseWebLayout())
        else:
            self.changeLayout(layout)

    @abstractmethod
    def render(self):
        pass

    @property
    def layout(self):
        return self._getLayout()

    def _getLayout(self):
        return self._layout

    def changeLayout(self, layout):
        if self._layout is not None:
            self._layout.deactivate()
        self._layout = layout
        self._layout.activate(self._experiment, self)

    def moveForward(self):
        if self._experiment.questionController.allowLeaving(Direction.FORWARD):
            self._experiment.questionController.currentQuestion._onHidingWidget()
            if self._experiment.questionController.canMoveForward:
                self._experiment.questionController.moveForward()
                self._experiment.savingAgentController.runSavingAgents(1)
            else:
                self._experiment.finish()
            self._experiment.questionController.currentQuestion._onShowingWidget()

    def moveBackward(self):
        if self._experiment.questionController.allowLeaving(Direction.BACKWARD):
            self._experiment.questionController.currentQuestion._onHidingWidget()
            self._experiment.questionController.moveBackward()
            self._experiment.savingAgentController.runSavingAgents(1)
            self._experiment.questionController.currentQuestion._onShowingWidget()

    def moveToPosition(self, posList):
        if self._experiment.questionController.allowLeaving(Direction.JUMP):
            self._experiment.questionController.currentQuestion._onHidingWidget()
            self._experiment.questionController.moveToPosition(posList)
            self._experiment.savingAgentController.runSavingAgents(1)
            self._experiment.questionController.currentQuestion._onShowingWidget()

    def start(self):
        self._experiment.questionController.enter()
        self._experiment.questionController.currentQuestion._onShowingWidget()


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
        self._experiment.questionController.currentQuestion.prepareWebWidget()

        jsScripts = []
        jsURLs = []
        cssScripts = []
        cssURLs = []

        # update with layout
        jsScripts = jsScripts + self._layout.javascriptCode
        jsURLs = jsURLs + self._layout.javascriptURLs
        cssScripts = cssScripts + self._layout.cssCode
        cssURLs = cssURLs + self._layout.cssURLs

        # update with currentQuestion
        jsScripts = jsScripts + self._experiment.questionController.currentQuestion.jsCode
        jsURLs = jsURLs + self._experiment.questionController.currentQuestion.jsURLs
        cssScripts = cssScripts + self._experiment.questionController.currentQuestion.cssCode
        cssURLs = cssURLs + self._experiment.questionController.currentQuestion.cssURLs

        # sort lists by first item
        jsScripts.sort(key=lambda x: x[0])
        jsURLs.sort(key=lambda x: x[0])
        cssScripts.sort(key=lambda x: x[0])
        cssURLs.sort(key=lambda x: x[0])

        # build html code
        html = "<!DOCTYPE html>\n<html><head><title>ALFRED</title>"

        for i, jsURL in jsURLs:
            html = html + "<script type=\"text/javascript\" src=\"%s\"></script>" % jsURL

        for i, jsScript in jsScripts:
            html = html + "<script type=\"text/javascript\">%s</script>" % jsScript

        for i, cssURL in cssURLs:
            html = html + "<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\" />" % cssURL

        for i, cssScript in cssScripts:
            html = html + "<style type=\"text/css\">%s</style>" % cssScript

        html = html + "</head><body><form id=\"form\" method=\"post\" action=\"%s/experiment\" autocomplete=\"off\" accept-charset=\"UTF-8\">" % self._basepath

        html = html + self._layout.render()

        html = html + "</form></body></html>"

        return html

    def renderHtml(self):
        return self.render()

    def getDynamicFile(self, identifier):
        fileObj, content_type = self._dynamicFilesDict[identifier]
        fileObj.seek(0)
        strIO = StringIO(fileObj.read())
        strIO.seek(0)
        return strIO, content_type

    def addDynamicFile(self, file_obj, content_type=None):
        identifier = uuid4().hex
        while identifier in self._dynamicFilesDict:
            identifier = uuid4().hex

        self._dynamicFilesDict[identifier] = (file_obj, content_type)
        return self._basepath + '/dynamicfile/' + identifier

    def getStaticFile(self, identifier):
        return self._staticFilesDict[identifier]

    def addStaticFile(self, path, content_type=None):
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

    def getCallable(self, identifier):
        return self._callablesDict[identifier]

    def addCallable(self, f):
        identifier = uuid4().hex
        while identifier in self._callablesDict:
            identifier = uuid4().hex

        self._callablesDict[identifier] = f
        return self._basepath + '/callable/' + identifier

    def updateWithUserInput(self, d):
        self._experiment.questionController.currentQuestion.setData(d)

    def jumpURLfromPosList(self, posList):
        return self._basepath + '/experiment?move=jump&par=' + '.'.join(posList)


try:
    class ThreadHelper(QtCore.QObject):
        renderSignal = QtCore.Signal()

        def __init__(self, uiController):
            super(ThreadHelper, self).__init__()
            self._uiController = uiController
            self.renderSignal.connect(self.renderSlot)

        def render(self):
            self.renderSignal.emit()

        @QtCore.Slot()
        def renderSlot(self):
            self._uiController.renderSlot()
except NameError:
    from .alfredlog import getLogger
    logger = getLogger((__name__))
    logger.warning("Can't create ThreadHelper. (Needed for Qt)")


class QtWebKitUserInterfaceController(WebUserInterfaceController):
    def __init__(self, experiment, weblayout=None, qtlayout=None, fullScreen=True, **kwargs):

        self._helper = ThreadHelper(self)

        localserver.setExperiment(experiment)

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

    def _getLayout(self):
        return self._layout

    def renderHtml(self):

        return super(QtWebKitUserInterfaceController, self).render()

    def render(self):
        self._helper.render()

    def renderSlot(self):

            # self._qtMainScrollArea.hide()
        self._webView.show()
        # TODO: Check if this fix is ok!
        # self._webView.load('http://127.0.0.1:5000/experiment')#http://127.0.0.1:5000/experiment

    def moveForward(self):

        super(QtWebKitUserInterfaceController, self).moveForward()

        self.render()

    def moveBackward(self):

        super(QtWebKitUserInterfaceController, self).moveBackward()

        self.render()

    def moveToPosition(self, posList):

        super(QtWebKitUserInterfaceController, self).moveForward()
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
        from .savingAgent import wait_for_saving_thread
        wait_for_saving_thread()
