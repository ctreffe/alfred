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

import alfred3.settings
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
        self._oldPage = None

        if layout is None:
            self.change_layout(BaseQtLayout() if experiment.type == 'qt' else BaseWebLayout())
        else:
            self.change_layout(layout)

        self._layout.forward_text = self._experiment._settings.navigation.forward
        self._layout.backward_text = self._experiment._settings.navigation.backward
        self._layout.finish_text = self._experiment._settings.navigation.finish
        
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
        if self._experiment.page_controller.allow_leaving(Direction.FORWARD):
            self._experiment.page_controller.current_page._on_hiding_widget()
            if self._experiment.page_controller.can_move_forward:
                self._experiment.page_controller.move_forward()
                self._experiment.saving_agent_controller.run_saving_agents(1)
            else:
                self._experiment.finish()
            self._experiment.page_controller.current_page._on_showing_widget()

    def move_backward(self):
        if self._experiment.page_controller.allow_leaving(Direction.BACKWARD):
            self._experiment.page_controller.current_page._on_hiding_widget()
            self._experiment.page_controller.move_backward()
            self._experiment.saving_agent_controller.run_saving_agents(1)
            self._experiment.page_controller.current_page._on_showing_widget()

    def move_to_position(self, pos_list):
        if self._experiment.page_controller.allow_leaving(Direction.JUMP):
            self._experiment.page_controller.current_page._on_hiding_widget()
            self._experiment.page_controller.move_to_position(pos_list)
            self._experiment.saving_agent_controller.run_saving_agents(1)
            self._experiment.page_controller.current_page._on_showing_widget()

    def start(self):
        self._experiment.page_controller.enter()
        self._experiment.page_controller.current_page._on_showing_widget()


class WebUserInterfaceController(UserInterfaceController):
    def __init__(self, experiment, layout=None):

        self._callables_dict = {}
        self._dynamic_files_dict = {}
        self._static_files_dict = {}
        self._basepath = alfred3.settings.webserver.basepath

        super(WebUserInterfaceController, self).__init__(experiment, layout)

    @property
    def basepath(self):
        return self._basepath

    def render(self, page_token):
        self._experiment.page_controller.current_page.prepare_web_widget()

        js_scripts = []
        js_urls = []
        css_scripts = []
        css_urls = []

        # update with layout
        js_scripts = js_scripts + self._layout.javascript_code
        js_urls = js_urls + self._layout.javascript_urls
        css_scripts = css_scripts + self._layout.css_code
        css_urls = css_urls + self._layout.css_urls

        # update with current_page
        js_scripts = js_scripts + self._experiment.page_controller.current_page.js_code
        js_urls = js_urls + self._experiment.page_controller.current_page.js_urls
        css_scripts = css_scripts + self._experiment.page_controller.current_page.css_code
        css_urls = css_urls + self._experiment.page_controller.current_page.css_urls

        # sort lists by first item
        js_scripts.sort(key=lambda x: x[0])
        js_urls.sort(key=lambda x: x[0])
        css_scripts.sort(key=lambda x: x[0])
        css_urls.sort(key=lambda x: x[0])

        # build html code
        html = "<!DOCTYPE html>\n<html><head><title>ALFRED</title>"

        for _, js_url in js_urls:
            html = html + "<script type=\"text/javascript\" src=\"%s\"></script>" % js_url

        for _, js_script in js_scripts:
            html = html + "<script type=\"text/javascript\">%s</script>" % js_script

        for _, css_url in css_urls:
            html = html + "<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\" />" % css_url

        for _, css_script in css_scripts:
            html = html + "<style type=\"text/css\">%s</style>" % css_script

        html = html + "</head><body><form id=\"form\" method=\"post\" action=\"%s/experiment\" autocomplete=\"off\" accept-charset=\"UTF-8\">" % self._basepath

        html = html + self._layout.render()

        html = html + "<input type=\"hidden\" name=\"page_token\" value=%s>" % page_token

        html = html + "</form></body></html>"

        return html

    def render_html(self, page_token):
        return self.render(page_token)

    def get_dynamic_file(self, identifier):
        file_obj, content_type = self._dynamic_files_dict[identifier]
        file_obj.seek(0)
        strIO = StringIO(file_obj.read())
        strIO.seek(0)
        return strIO, content_type

    def add_dynamic_file(self, file_obj, content_type=None):
        identifier = uuid4().hex
        while identifier in self._dynamic_files_dict:
            identifier = uuid4().hex

        self._dynamic_files_dict[identifier] = (file_obj, content_type)
        url = '{basepath}/dynamicfile/{identifier}'.format(basepath=self._basepath, identifier=identifier)
        return url

    def get_static_file(self, identifier):
        return self._static_files_dict[identifier]

    def add_static_file(self, path, content_type=None):
        if not os.path.isabs(path):
            path = self._experiment.subpath(path)

        identifier = uuid4().hex

        if alfred3.settings.debugmode:
            if not hasattr(self, 'sf_counter'):
                self.sf_counter = 0
            self.sf_counter += 1
            identifier = str(self.sf_counter)

        while identifier in self._static_files_dict:
            identifier = uuid4().hex

        self._static_files_dict[identifier] = (path, content_type)
        url = '{basepath}/staticfile/{identifier}'.format(basepath=self._basepath, identifier=identifier)
        return url

    def get_callable(self, identifier):
        return self._callables_dict[identifier]

    def add_callable(self, f):
        identifier = uuid4().hex
        while identifier in self._callables_dict:
            identifier = uuid4().hex

        self._callables_dict[identifier] = f
        url = '{basepath}/callable/{identifier}'.format(basepath=self._basepath, identifier=identifier)
        return url

    def update_with_user_input(self, d):
        self._experiment.page_controller.current_page.set_data(d)

    def jump_url_from_pos_list(self, pos_list):
        return self._basepath + '/experiment?move=jump&par=' + '.'.join(pos_list)


try:
    class ThreadHelper(QtCore.QObject):
        render_signal = QtCore.Signal()

        def __init__(self, ui_controller):
            super(ThreadHelper, self).__init__()
            self._ui_controller = ui_controller
            self.render_signal.connect(self.render_slot)

        def render(self):
            self.render_signal.emit()

        @QtCore.Slot()
        def render_slot(self):
            self._ui_controller.render_slot()
except NameError:
    from .alfredlog import getLogger
    logger = getLogger((__name__))
    logger.warning("Can't create ThreadHelper. (Needed for Qt)")


class QtWebKitUserInterfaceController(WebUserInterfaceController):
    def __init__(self, experiment, weblayout=None, qtlayout=None, full_scren=True, **kwargs):

        self._helper = ThreadHelper(self)

        localserver.script.set_experiment(experiment)

        # initialize qt
        self._app = QApplication([])
        self._qt_window = QMainWindow()
        self._qt_window.setMinimumHeight(720)
        self._qt_window.setMinimumWidth(1024)
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self._web_view = QWebView()
        # self._qt_main_scroll_area = QScrollArea()
        # self._qt_main_scroll_area.set_widget_resizeable(True)  # Must be set to True in order for layout to work properly
        # self._qt_main_scroll_area.set_style_sheet("QScrollArea {background: white; border: none}")

        layout.addWidget(self._web_view)

        self._qt_window.setCentralWidget(widget)

        self._current_main_widget = None
        # self._qtlayout = None

        self._fullscreen = full_scren

        super(QtWebKitUserInterfaceController, self).__init__(experiment, weblayout)
        # self.change_qt_layout(qtlayout or BaseQtLayout())

    def _get_layout(self):
        return self._layout

    def render_html(self, page_token):

        return super(QtWebKitUserInterfaceController, self).render(page_token)

    def render(self):
        self._helper.render()

    def render_slot(self):

            # self._qt_main_scroll_area.hide()
        self._web_view.show()
        # TODO: Check if this fix is ok!
        # self._web_view.load('http://127.0.0.1:5000/experiment')#http://127.0.0.1:5000/experiment

    def move_forward(self):

        super(QtWebKitUserInterfaceController, self).move_forward()

        self.render()

    def move_backward(self):

        super(QtWebKitUserInterfaceController, self).move_backward()

        self.render()

    def move_to_position(self, pos_list):

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
        self._web_view.setUrl("http://127.0.0.1:5000/experiment")

        if self._fullscreen:
            self._qt_window.show_full_screen()
        else:
            self._qt_window.show()

        self.render()
        self._app.exec_()

        # after leaving app this code will be executed
        from .saving_agent import wait_for_saving_thread
        wait_for_saving_thread()
