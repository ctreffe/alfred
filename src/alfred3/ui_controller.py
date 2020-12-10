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
from dataclasses import dataclass

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

@dataclass
class Move:
    """Template for saving data about participant movements.
    
    Attributes:
        move_number: A continuously increasing counter of moves. Starts
            at one.
        tree: The full hierarchy of sections, indicating the exact 
            position of the Move's *page* in the experiment.
        page_name: The name of the Move's page.
        section_allows_backward: Indicates, whether participants can move
            backward from the Move's page.
        section_allows_forward: Indicates, whether participants can move
            forward from the Move's page.
        section_allows_jumpfrom: Indicates, whether participants can 
            jump from the Move's page.
        section_allows_jumpto: Indicates, whether participants can 
            jump to the Move's page.
        show_time: Time when the page was shown in seconds since epoch.
        hide_time: Time when the page was hidden in seconds since epoch.
        duration: Duration in seconds, calculated as the difference 
            hidetime - showtime.
        page_status_before_visit: Indicates the page's status before
            the visit represented by the Move instance, e.g. 'open', or 
            'closed'.
        page_status_before_visit: Indicates the page's status after
            the visit represented by the Move instance, e.g. 'open', or 
            'closed'.
        leave_in_direction: Indicates the direction, in which the page 
            was left (e.g. 'forward', 'backward', or 'jump').
    
    """

    move_number: int = None
    tree: str = None
    page_name: str = None
    show_time: float = None
    hide_time: float = None
    duration: float = None
    page_status_before_visit: str = None
    page_status_after_visit: str = None
    leave_in_direction: str = None
    section_allows_forward: bool = None
    section_allows_backward: bool = None
    section_allows_jumpfrom: bool = None
    section_allows_jumpto: bool = None


class MovementManager:

    def __init__(self, experiment):
        self.exp = experiment
        self.experiment = experiment
        self.current_index: int = 0
        self.previous_index: int = 0
        self.history: list = []
    
    
    @property
    def current_page(self):
        i = self.current_index
        return self.exp.root_section.all_pages_list[i]
    
    @property
    def previous_page(self):
        if self.current_page is self.first_page:
            return None
        
        i = self.previous_index
        return self.exp.root_section.all_pages_list[i]
    
    @property
    def next_page(self):
        # if self.current_page is self.last_page:
        #     return None

        i = self.current_index + 1
        return self.exp.root_section.all_pages_list[i]
    
    @property
    def last_page(self):
        return self.exp.root_section.all_pages_list[-1]
    
    @property
    def first_page(self):
        return self.exp.root_section.all_pages_list[0]
    
    def _move(self, to_page, direction: str):
        current_page = self.current_page

        if not current_page.section.allow_move(direction=direction):
            return False

        current_page._on_hiding_widget()
        page_was_closed = current_page.is_closed
        
        if current_page.section is not to_page.section:
            current_page.section.leave()
            self.record_move(page_was_closed, direction=direction)
            to_page.section.enter()
        else:
            current_page.section.move(direction=direction)
            self.record_move(page_was_closed, direction=direction)
        
        return True
    
    def forward(self):
        if not self.current_page.section.allow_forward:
            return False

        if self._move(to_page=self.next_page, direction="forward"):
            self.previous_index = self.current_index
            self.current_index += 1

            if not self.current_page.should_be_shown:
                return self.forward()

            return True
        
        else:
            return False
    
    def backward(self):
        if not self.current_page.section.allow_backward:
            return False

        if self._move(to_page=self.next_page, direction="backward"):
            self.previous_index = self.current_index
            self.current_index -= 1

            if not self.current_page.should_be_shown:
                return self.backward()

            return True
        
        else:
            return False
    
    def jump_by_name(self, name: str):
        next_page = self.exp.root_section.members[name]
        
        if not self.current_page.section.allow_jumpfrom:
            return False
        elif not next_page.section.allow_jumpto:
            return False
        
        if self._move(to_page=next_page, direction="jump"):
            self.previous_index = self.current_index
            self.current_index = self.exp.root_section.all_pages_list.index(name)
            return True
        
        else:
            return False
    
    def jump_by_index(self, index: int):
        next_page = self.exp.root_section.all_pages_list[index]

        if not self.current_page.section.allow_jumpfrom:
            return False
        elif not next_page.section.allow_jumpto:
            return False
        
        if self._move(to_page=next_page, direction="jump"):
            self.previous_index = self.current_index
            self.current_index = index
            return True
        
        else:
            return False

    def record_move(self,page_was_closed: bool, direction: str):
        current_page = self.current_page
        
        move = Move()
        move.move_number = len(self.history) + 1
        move.tree = current_page.tree
        move.page_name = current_page.name
        move.page_status_before_visit = "closed" if page_was_closed else "open"
        move.page_status_after_visit = "closed" if current_page.is_closed else "open"
        move.show_time = current_page.show_times[-1]
        move.hide_time = current_page.hide_times[-1]
        move.duration = move.hide_time - move.show_time
        move.section_allows_forward = current_page.section.allow_forward
        move.section_allows_backward = current_page.section.allow_backward
        move.section_allows_jumpfrom = current_page.section.allow_jumpfrom
        move.section_allows_jumpto = current_page.section.allow_jumpto
        move.leave_in_direction = direction
        self.history.append(move)

class UserInterface:
    _css_files = [
        "bootstrap-4.5.3.min.css",
        "prism.css",
        "font-awesome-icons.css",
        "responsive.css",
    ]

    _js_files = [
        "jquery-3.5.1.min.js",
        "popper.min.js",
        "bootstrap-4.5.3.min.js",
        "detect.min.js",
        "prism.js",
        "font-awesome-icons.js",
        "responsive.js",

    ]

    def __init__(self, experiment):
        self.template = jinja_env.get_template("page.html.j2")

        self.experiment = experiment
        self.log = QueuedLoggingInterface(base_logger=__name__)
        self.log.add_queue_logger(self, __name__)

        self._basepath = self.experiment.config.get("webserver", "basepath")
        self._static_files = {}
        self._dynamic_files = {}
        self._callables = {}

        self.config = {}
        self.config["responsive"] = self.experiment.config.getboolean("layout", "responsive")
        self.config["website_title"] = self.experiment.config.get("layout", "website_title")
        self.config["logo_text"] = self.experiment.config.get("layout", "logo_text")
        self.config["footer_text"] = self.experiment.config.get("layout", "footer_text")

        with importlib.resources.path(img, "alfred_logo_color.png") as p:
            self.config["alfred_logo_url"] = self.add_static_file(p, content_type="image/png")

        self.css_urls = []
        self.js_urls = []

        self.css_code = []
        self.js_code = []

        
        self._determine_style()


        self._callables["clientinfo"] = self.save_client_info

        self.forward_enabled = True
        self.backward_enabled = True
        self.finish_enabled = True
        
        # the code block below enables the creation of standalone alfred3 html pages,
        # which don't host their own JavaScript and CSS on a localserver,
        # but instead place it directly in the html file.
        debug = self.experiment.config.getboolean("general", "debug")
        code_in_template = self.experiment.config.getboolean("debug", "code_in_templates")
        if debug and code_in_template:
            self._add_resources(self._js_files, "js")
            self._add_resources(self._css_files, "css")
        else:
            self._add_resource_links(self._js_files, "js")
            self._add_resource_links(self._css_files, "css")

    @property
    def exp(self):
        return self.experiment

    def _determine_style(self):
        """Adds .css styles and logo image to the layout.
        
        This method manages the switch between the two builtin styles 
        'base' and 'goe', and a possible customly defined style. If 
        reads the option "style" in the section "layout" of config.conf.
        """
        style = self.experiment.config.get("layout", "style")

        if style == "base":
            with importlib.resources.path(css, "base.css") as f:
                url = self.add_static_file(f, content_type="text/css")
                self.css_urls.append((10, url))

        elif style == "goe":

            with importlib.resources.path(css, "goe.css") as f:
                url = self.add_static_file(f, content_type="text/css")
                self.css_urls.append((10, url))

            with importlib.resources.path(img, "uni_goe_logo_white.png") as p:
                url = self.add_static_file(p, content_type="image/png")
                self.config["logo_url"] = url

        elif style.endswith(".css"):
            path = self.experiment.subpath(style)
            url = self.add_static_file(path, content_type="text/css")
            self.css_urls.append((10, url))

            logo = self.experiment.config.get("layout", "logo")
            logo_path = self.experiment.subpath(logo)
            if logo_path.suffix == ".png":
                content_type = "image/png"
            elif logo_path.suffix in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            logo_url = self.add_static_file(logo_path, content_type=content_type)
            self.config["logo_url"] = logo_url

        else:
            raise ValueError(
                "Config option 'style' in section 'layout' must be 'base', 'goe', or a valid path to a .css file."
            )

    def _add_resource_links(self, resources: list, resource_type: str):
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

    def save_client_info(self, **data):
        """Updates the client info dictionary and saves data."""

        self.experiment.data_manager.client_info.update(data)
        self.experiment.page_controller.current_page.save_data()

    def _add_resources(self, resources: list, resource_type: str):

        if resource_type == "js":
            container = self.js_code
            pkg = js
        elif resource_type == "css":
            container = self.css_code
            pkg = css

        for i, f in enumerate(resources):
            container.append((i, importlib.resources.read_text(pkg, f)))

    def code(self, page) -> dict:
        """Wraps the basic layout CSS and JavaScript together with
        the page's CSS and JavaScript in a single dictionary
        for easy use.
        """

        code = {}

        code["layout_css"] = sorted(self.css_urls)
        code["layout_js"] = sorted(self.js_urls)
        code["layout_css_code"] = sorted(self.css_code)
        code["layout_js_code"] = sorted(self.js_code)

        code["css_urls"] = page.css_urls
        code["css_code"] = page.css_code
        code["js_urls"] = page.js_urls
        code["js_code"] = page.js_code

        # JS Code for a single data saving call upon a visit to the first page
        # This is necessary in order to also save the screen resolution
        first_page = self.exp.movement_manager.first_page
        if page is first_page and self.experiment.config.getboolean("general", "save_client_info"):
            code["js_code"] += [(7, importlib.resources.read_text(js, "clientinfo.js"))]

        return code

    def render(self, page_token):
        """Renders the current page."""

        page = self.experiment.movement_manager.current_page
        page.prepare_web_widget()

        d = {**self.config}

        d["code"] = self.code(page=page)
        d["page_token"] = page_token
        d["elements"] = page.elements.values()

        d["title"] = page.title
        d["subtitle"] = page.subtitle
        if page.statustext:
            d["statustext"] = page.statustext
        
        if not page.can_display_corrective_hints_in_line:
            d["corrective_hints"] = page.corrective_hints
        
        if page.section.allow_backward and not page is self.exp.movement_manager.first_page:
            d["backward_text"] = self.experiment.config.get("navigation", "backward")
        
        if page.section.allow_forward:
            if self.exp.movement_manager.next_page is self.exp.root_section.final_page:
                d["finish_text"] = self.experiment.config.get("navigation", "finish")
            else:
                d["forward_text"] = self.experiment.config.get("navigation", "forward")

        messages = self.experiment.message_manager.get_messages()
        if messages:
            for message in messages:
                message.level = (
                    "" if message.level == "warning" else "alert-" + message.level
                )  # level to bootstrap
            d["messages"] = messages

        # progress bar
        n_el = len(self.experiment.page_controller.all_input_elements)
        n_pg = len(self.experiment.page_controller.all_pages)
        i_el = len(self.experiment.page_controller.all_filled_input_elements)
        i_pg = len(self.experiment.page_controller.all_shown_pages)
        exact_progress = ((i_el + i_pg) / (n_el + n_pg)) * 100
        if not self.experiment.finished:
            d["progress"] = min(round(exact_progress, 1), 95)
        else:
            d["progress"] = 100
        d["show_progress"] = self.experiment.config.getboolean("layout", "show_progress")
        d["fix_progress_top"] = self.experiment.config.getboolean("layout", "fix_progress_top")

        return self.template.render(d)

    def render_html(self, page_token):
        """Alias for render, provided for compatibility."""
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
        if self.experiment.config.getboolean("general", "debug"):
            return path

        path = Path(path)
        if not path.is_absolute():
            path = self.experiment.path / path

        identifier = uuid4().hex

        # the code below causes alfred to fail to detect changes in
        # static files when debug mode is activated

        # if self.experiment and self.experiment.config.getboolean("general", "debug"):
        #     if not hasattr(self, "sf_counter"):
        #         self.sf_counter = 0
        #     self.sf_counter += 1
        #     identifier = str(self.sf_counter)

        self._static_files[identifier] = (path, content_type)

        url = f"{self.basepath}/staticfile/{identifier}"
        return url

    def get_dynamic_file(self, identifier):
        return self._dynamic_files[identifier]

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

    def start(self):
        self.experiment.page_controller.enter()


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
            self._experiment.page_controller.move_forward()

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

        # the code below causes alfred to fail to detect changes in
        # static files when debug mode is activated

        # if self._experiment.config.getboolean("general", "debug"):
        #     if not hasattr(self, "sf_counter"):
        #         self.sf_counter = 0
        #     self.sf_counter += 1
        #     identifier = str(self.sf_counter)

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
