# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

Das Modul *ui_controller* stellt die Klassen zur Verfügung, die die Darstellung und die Steuerelemente auf verschiedenen Interfaces verwalten.
"""
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

from ._core import Direction
from .layout import BaseWebLayout

from .helpmates import localserver as localserver
from .alfredlog import QueuedLoggingInterface
from future.utils import with_metaclass


class UserInterfaceController(with_metaclass(ABCMeta, object)):
    """
    Abstrakte Basisklasse, die die Grundfunktionalität für alle UserIntferaces bereitstellt

    """

    def __init__(self, experiment, layout=None):
        """
        :param experiment: Ein Objekt vom Typ Experiment
        :param layout: Ein Objekt vom Typ Layout (None bedeutet Standardlayout)

        |

        Bei Aufruf der Klasse wird mittels :meth:`.change_layout` ein :attr:`.layout` gesetzt.

        """
        self._experiment = experiment
        self._layout = None
        self._oldPage = None
        self.log = QueuedLoggingInterface(base_logger=__name__, queue_logger=self.prepare_logger_name())
        self.log.session_id = self.experiment.config.get("metadata", "session_id")

        if layout is None:
            self.change_layout(BaseWebLayout())
        else:
            self.change_layout(layout)

        self._layout.forward_text = self._experiment.config.get("navigation", "forward")
        self._layout.backward_text = self._experiment.config.get("navigation", "backward")
        self._layout.finish_text = self._experiment.config.get("navigation", "finish")

    @property
    def experiment(self):
        return self._experiment

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
    
    def prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name.class_uid
        
        with *class_uid* only added, if 
        :attr:`~Section.instance_level_logging` is set to *True*.
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self.experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        return ".".join(name)


class WebUserInterfaceController(UserInterfaceController):
    def __init__(self, experiment, layout=None):

        self._callables_dict = {}
        self._dynamic_files_dict = {}
        self._static_files_dict = {}
        self._basepath = experiment.config.get("webserver", "basepath")

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
            html = html + '<script type="text/javascript" src="%s"></script>' % js_url

        for _, js_script in js_scripts:
            html = html + '<script type="text/javascript">%s</script>' % js_script

        for _, css_url in css_urls:
            html = html + '<link rel="stylesheet" type="text/css" href="%s" />' % css_url

        for _, css_script in css_scripts:
            html = html + '<style type="text/css">%s</style>' % css_script

        html = (
            html
            + '</head><body><form id="form" method="post" action="%s/experiment" autocomplete="off" accept-charset="UTF-8">'
            % self._basepath
        )

        html = html + self._layout.render()

        html = html + '<input type="hidden" name="page_token" value=%s>' % page_token

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
        url = "{basepath}/dynamicfile/{identifier}".format(
            basepath=self._basepath, identifier=identifier
        )
        return url

    def get_static_file(self, identifier):
        return self._static_files_dict[identifier]

    def add_static_file(self, path, content_type=None):
        if not os.path.isabs(path):
            path = self._experiment.subpath(path)

        identifier = uuid4().hex
        

        if self._experiment.config.getboolean("general", "debug"):
            if not hasattr(self, "sf_counter"):
                self.sf_counter = 0
            self.sf_counter += 1
            identifier = str(self.sf_counter)

        while identifier in self._static_files_dict:
            identifier = uuid4().hex

        self._static_files_dict[identifier] = (path, content_type)
        url = "{basepath}/staticfile/{identifier}".format(
            basepath=self._basepath, identifier=identifier
        )
        return url

    def get_callable(self, identifier):
        return self._callables_dict[identifier]

    def add_callable(self, f):
        identifier = uuid4().hex
        while identifier in self._callables_dict:
            identifier = uuid4().hex

        self._callables_dict[identifier] = f
        url = "{basepath}/callable/{identifier}".format(
            basepath=self._basepath, identifier=identifier
        )
        return url

    def update_with_user_input(self, d):
        self._experiment.page_controller.current_page.set_data(d)

    def jump_url_from_pos_list(self, pos_list):
        return self._basepath + "/experiment?move=jump&par=" + ".".join(pos_list)
