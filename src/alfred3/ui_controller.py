# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

Das Modul *ui_controller* stellt die Klassen zur Verfügung, die die Darstellung und die Steuerelemente auf verschiedenen Interfaces verwalten.
"""
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
import os
import threading
from abc import ABCMeta, abstractmethod
from builtins import object, str
from io import StringIO
from pathlib import Path
from uuid import uuid4

import importlib.resources

from future.utils import with_metaclass
from jinja2 import Environment, PackageLoader

from ._core import Direction
from .alfredlog import QueuedLoggingInterface
from .helpmates import localserver as localserver
from .layout import BaseWebLayout
from .static import js
from .static import css
from .static import img

jinja_env = Environment(loader=PackageLoader("alfred3", "templates"))


class UserInterface:
    _css_files = ["bootstrap-4.5.3.min.css", "prism.css", "responsive.css", "layout_goe.css"]

    _js_files = [
        "jquery-3.5.1.min.js",
        "popper.min.js",
        "bootstrap-4.5.3.min.js",
        "prism.js",
        "responsive.js",
    ]

    _logo = "uni_goe_logo_white.png"
    _alfred_logo = "alfred_logo_color.png"

    def __init__(self, experiment):
        self.template = jinja_env.get_template("page.html")

        self.experiment = experiment
        self.log = QueuedLoggingInterface(
            base_logger=__name__, queue_logger=self.prepare_logger_name()
        )
        self._basepath = self.experiment.config.get("webserver", "basepath")
        self._static_files = {}
        self._dynamic_files = {}
        self._callables = {}

        self.config = {}
        self.config["responsive"] = self.experiment.config.getboolean("layout", "responsive")
        self.config["website_title"] = self.experiment.config.get("layout", "website_title")
        self.config["logo_url"] = self.add_logo()
        self.config["logo_text"] = self.experiment.config.get("layout", "logo_text")
        self.config["footer_text"] = self.experiment.config.get("layout", "footer_text")

        with importlib.resources.path(img, self._alfred_logo) as p:
            self.config["alfred_logo_url"] = self.add_static_file(p, content_type="image/png")

        self.css_urls = []
        self.js_urls = []

        self._add_resources(self._js_files, "js")
        self._add_resources(self._css_files, "css")

        self.forward_enabled = True
        self.backward_enabled = True
        self.finish_enabled = True

    def add_logo(self):
        custom_logo = self.experiment.config.get("layout", "logo")

        if custom_logo:
            logo_path = Path(custom_logo).resolve()
            if not logo_path.is_absolute():
                logo_path = self.experiment.path / logo_path

            if logo_path.suffix == ".png":
                content_type = "image/png"
            elif logo_path.suffix == ".jpg" or logo_path.suffix == ".jpeg":
                content_type = "image/jpeg"

            return self.add_static_file(logo_path, content_type=content_type)

        else:
            with importlib.resources.path(img, self._logo) as p:
                url = self.add_static_file(p, content_type="image/png")

            return url

    def _add_resources(self, resources: list, resource_type: str):
        """Adds resources to the UI via add_static_file.
        
        Args:
            resources: A list of tuples of the form (pkg, resource).
            resource_typetype: A string indicating the type of resource. 
                "js" for JavaScript, "css" for Cascading Style Sheets.
        """

        if resource_type == "js":
            container = self.js_urls
            pkg = js
        elif resource_type == "css":
            container = self.css_urls
            pkg = css

        for i, f in enumerate(resources):
            with importlib.resources.path(pkg, f) as p:
                url = self.add_static_file(p)
                container.append((i, url))

    def code(self, page):
        """Wraps the basic layout CSS and JavaScript together with
        the page's CSS and JavaScript in a single dictionary
        for easy use.
        """

        code = {}

        code["layout_css"] = self.css_urls
        code["layout_js"] = self.js_urls

        code["css_urls"] = page.css_urls
        code["css_code"] = page.css_code
        code["js_urls"] = page.js_urls
        code["js_code"] = page.js_code

        return code

    def render(self, page_token):
        """Renders the current page."""

        page = self.experiment.page_controller.current_page
        page.prepare_web_widget()

        code = self.code(page=page)

        d = {**self.config}

        d["title"] = self.experiment.page_controller.current_title
        d["subtitle"] = self.experiment.page_controller.current_subtitle
        d["page_token"] = page_token

        if self.experiment.page_controller.current_status_text:
            d["statustext"] = self.experiment.page_controller.current_status_text

        if (
            not self.experiment.page_controller.current_page.can_display_corrective_hints_in_line
            and self.experiment.page_controller.current_page.corrective_hints
        ):
            d["corrective_hints"] = self.experiment.page_controller.current_page.corrective_hints

        if self.backward_enabled:
            if self.experiment.page_controller.can_move_backward:
                d["backward_text"] = self.experiment.config.get("navigation", "backward")

        if self.forward_enabled:
            if self.experiment.page_controller.can_move_forward:
                d["forward_text"] = self.experiment.config.get("navigation", "forward")
            elif self.finish_enabled and not self.experiment.finished:
                d["finish_text"] = self.experiment.config.get("navigation", "finish")

        messages = self.experiment.message_manager.get_messages()
        if messages:
            for message in messages:
                message.level = (
                    "" if message.level == "warning" else "alert-" + message.level
                )  # level to bootstrap
            d["messages"] = messages

        return self.template.render(d=d, element_list=page.element_list, code=code)

    def render_html(self, page_token):
        """Alia for render, provided for compatibility."""
        return self.render(page_token=page_token)

    @property
    def basepath(self):

        if self._basepath is not None:
            return self._basepath
        else:
            return ""

    def get_static_file(self, identifier):
        """Returns the filepath to a static file based on its unique ID.

        Args:
            identifier: Unique ID of a static file.
        """
        return self._static_files[identifier]

    def add_static_file(self, path, content_type=None):
        """Adds a static file to an internal list. This allows us to
        keep the actual filepath private, which is a security feature
        for web experiments.

        Returns the anonymized url for the added file.

        Args:
            path: Path to file.
            content_type: Mimetype of the added file.
        """
        path = Path(path)
        if not path.is_absolute():
            path = self.experiment.path / path

        identifier = uuid4().hex

        if self.experiment and self.experiment.config.getboolean("general", "debug"):
            if not hasattr(self, "sf_counter"):
                self.sf_counter = 0
            self.sf_counter += 1
            identifier = str(self.sf_counter)

        self._static_files[identifier] = (path, content_type)

        url = f"{self.basepath}/staticfile/{identifier}"
        return url

    def get_dynamic_file(self, identifier):
        file_obj, content_type = self._dynamic_files[identifier]
        file_obj.seek(0)
        strIO = StringIO(file_obj.read())
        strIO.seek(0)
        return strIO, content_type

    def add_dynamic_file(self, file_obj, content_type=None):
        identifier = uuid4().hex
        while identifier in self._dynamic_files:
            identifier = uuid4().hex

        self._dynamic_files[identifier] = (file_obj, content_type)
        url = "{basepath}/dynamicfile/{identifier}".format(
            basepath=self._basepath, identifier=identifier
        )
        return url

    def get_callable(self, identifier):
        return self._callables[identifier]

    def add_callable(self, f: callable):
        identifier = uuid4().hex
        while identifier in self._callables:
            identifier = uuid4().hex

        self._callables[identifier] = f
        url = "{basepath}/callable/{identifier}".format(
            basepath=self._basepath, identifier=identifier
        )
        return url

    def move_forward(self):
        if self.experiment.page_controller.allow_leaving(Direction.FORWARD):
            self.experiment.page_controller.current_page._on_hiding_widget()
            if self.experiment.page_controller.can_move_forward:
                self.experiment.page_controller.move_forward()
            else:
                self.experiment.finish()

    def move_backward(self):
        if self.experiment.page_controller.allow_leaving(Direction.BACKWARD):
            self.experiment.page_controller.current_page._on_hiding_widget()
            self.experiment.page_controller.move_backward()

    def start(self):
        self.experiment.page_controller.enter()

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
        self.log = QueuedLoggingInterface(
            base_logger=__name__, queue_logger=self.prepare_logger_name()
        )
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
            else:
                self._experiment.finish()

    def move_backward(self):
        if self._experiment.page_controller.allow_leaving(Direction.BACKWARD):
            self._experiment.page_controller.current_page._on_hiding_widget()
            self._experiment.page_controller.move_backward()

    def move_to_position(self, pos_list):
        if self._experiment.page_controller.allow_leaving(Direction.JUMP):
            self._experiment.page_controller.current_page._on_hiding_widget()
            self._experiment.page_controller.move_to_position(pos_list)

    def start(self):
        self._experiment.page_controller.current_page.save_data()
        self._experiment.page_controller.enter()

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
