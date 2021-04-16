# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

Das Modul *ui_controller* stellt die Klassen zur Verfügung, die die Darstellung und die Steuerelemente auf verschiedenen Interfaces verwalten.
"""
import os
import threading
import time

from abc import ABCMeta, abstractmethod
from io import StringIO
from pathlib import Path
from uuid import uuid4
from dataclasses import dataclass
from typing import Union, Tuple

import importlib.resources
from jinja2 import Environment, PackageLoader

from .alfredlog import QueuedLoggingInterface
from .static import js
from .static import css
from .static import img
from . import element as elm
from .exceptions import AlfredError, ValidationError, AbortMove
from .util import icon

jinja_env = Environment(loader=PackageLoader("alfred3", "templates"))

@dataclass
class Move:
    """
    Template for saving data about participant movements.
    
    Attributes:
        exp_title: Experiment title
        exp_author: Experiment author
        exp_version: Experiment version
        exp_id: Experiment id
        exp_session_id: Experiment session id

        move_number: A continuously increasing counter of moves. Starts
            at one.
        tree: The full hierarchy of sections, indicating the exact 
            position of the Move's *page* in the experiment.
        page_name: The name of the Move's page.
        
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
        previous_page: Name of the previous page
        target_page: Name of the next page
        
        section_allows_backward: Indicates, whether participants can move
            backward from the Move's page.
        section_allows_forward: Indicates, whether participants can move
            forward from the Move's page.
        section_allows_jumpfrom: Indicates, whether participants can 
            jump from the Move's page.
        section_allows_jumpto: Indicates, whether participants can 
            jump to the Move's page.
    
    """
    exp_title: str = None
    exp_author: str = None
    exp_version: str = None
    exp_id: str = None
    exp_session_id: str = None
    
    move_number: int = None
    tree: str = None
    page_name: str = None
    
    show_time: float = None
    hide_time: float = None
    duration: float = None
    
    page_status_before_visit: str = None
    page_status_after_visit: str = None
    
    leave_in_direction: str = None
    previous_page: str = None
    target_page: str = None
    
    section_allows_forward: bool = None
    section_allows_backward: bool = None
    section_allows_jumpfrom: bool = None
    section_allows_jumpto: bool = None


class MovementManager:
    instance_log = False

    def __init__(self, experiment):
        self.exp = experiment
        self.experiment = experiment
        self.log = QueuedLoggingInterface(base_logger=__name__)
        self.log.add_queue_logger(self, __name__)

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
        if self.current_page is self.final_page:
            return None
        i = self.current_index + 1
        return self.exp.root_section.all_pages_list[i]
    
    @property
    def final_page(self):
        return self.exp.final_page
    
    def page_after(self, page):
        i = self.exp.root_section.all_page_names.index(page.name) + 1
        return self.exp.root_section.all_pages_list[i]
    
    def page_before(self, page):
        if self.current_page is self.first_page:
            return None
        i = self.exp.root_section.all_page_names.index(page.name) - 1
        return self.exp.root_section.all_pages_list[i]

    def find_page(self, query: Union[str, int]):
        """
        Find a page.

        Args:
            query: Can be either a page name or a page index.
        """
        page = self.experiment.root_section.all_pages.get(query, None)
        if page is not None:
            return page
        else:
            try:
                page = self.exp.root_section.all_pages_list[int(query)]
                return page
            except (IndexError, TypeError, ValueError):
                return None

    def index_of(self, page):
        return self.experiment.root_section.all_page_names.index(page.name)

    @property
    def first_page(self):
        return self.exp.root_section.all_pages_list[0]
    
    @property
    def first_visible_page(self):
        i = 0
        pages = self.exp.root_section.all_pages_list
        while not pages[i].should_be_shown:
            i += 1
        return pages[i]
    
    @property
    def last_page(self):
        return self.exp.root_section.all_pages_list[-2]
    
    def _abort_move(self):
        return self.current_index, self.current_index
    
    def _skip_page(self, to_page, direction: str) -> Tuple[int, int]:
        """
        Returns:
            Tuple[int, int]: A tuple of the current page and the target 
                page.

        Raises:
            AbortMove: If the movement is a jump and the target page
                (*to_page*) should not be shown.
        """
        if direction == "forward":
            self.log.debug(f"{to_page} should not be shown. Skipping page in direction 'forward'.")
            return self._move(to_page=self.page_after(to_page), direction="forward")
    
        elif direction == "backward":
            self.log.debug(f"{to_page} should not be shown. Skipping page in direction 'backward'.")
            return self._move(to_page=self.page_before(to_page), direction="backward")
    
        elif direction == "jump":
            self.log.debug(f"{to_page} should not be shown. Aborting move.")
            if self.exp.config.getboolean("general", "debug"):
                self.exp.message_manager.post_message(f"{to_page} should not be shown. Jump was aborted.", level="debug")
            raise AbortMove()
    
    def _check_permissions(self, to_page, direction: str):
        # check section permissions for jumps
        if direction == "jump":
            jump_allowed = self._check_jump_permission(next_page=to_page)
            if not jump_allowed:
                raise AbortMove()
        
        # check section permissions for normal moves
        elif not getattr(self.current_page.section, "allow_" + direction):
            self.log.debug(f"Section of page {self.current_page} does not allow movement in direction '{direction}'")
            raise AbortMove()
        
        # check section permission for target section
        elif direction == "backward" and not to_page.section.allow_backward:
            self.log.debug(f"Section of page {to_page} does not allow movement in direction '{direction}'")
            raise AbortMove()
    
    def _switch_sections(self, from_page, to_page, direction: str):
        page_status_before = from_page.is_closed
        
        if direction == "jump":
            from_page.section._move("jumpfrom")
        else:
            from_page.section._move(direction)

        if to_page.section.name in from_page.section.all_members:
            from_page.section._hand_over()
        else:
            from_page.section._leave()

        if self.exp.config.getboolean("data", "record_move_history"):
            self.record_move(page_status_before, direction=direction, to_page=to_page)
        
        if direction == "jump":
            to_page.section._move("jumpto")

        if from_page.section.name in to_page.section.all_members:
            to_page.section._resume()
        else:
            to_page.section._enter()
            
    def _conduct_movement(self, to_page, direction: str) -> Tuple[int, int]:
        """
        Raises:
            AbortMove: If section validation does not succeed.
        """
        current_page = self.current_page
        
        if not to_page.should_be_shown:
            # Executed here first for possibility of early cancellation
            return self._skip_page(to_page=to_page, direction=direction)
        
        # check section permissions for jumps
        self._check_permissions(to_page=to_page, direction=direction)

        self.log.debug(f"Moving from {self.current_page} to {to_page}, direction: '{direction}'.")

        # management of section entering and leaving behavior
        # and recording the move
        page_status_before = current_page.is_closed
        if current_page.section is not to_page.section:
            try:
                self._switch_sections(from_page=current_page, to_page=to_page, direction=direction)
            except ValidationError:
                raise AbortMove()
        
        else:
            try:
                if direction == "jump":
                    current_page.section._move("jumpfrom")
                    current_page.section._move("jumpto")
                else:
                    current_page.section._move(direction)
            except ValidationError:
                raise AbortMove()

            if self.exp.config.getboolean("data", "record_move_history"):
                self.record_move(page_status_before, direction=direction, to_page=to_page)

        now = time.time()
        to_page._on_showing_widget(show_time=now)

        if not to_page.should_be_shown:
        # executed here a second time, in case the to_page's 
        # should_be_shown attribute was changed during any of the move
        # functions

            return self._skip_page(to_page=to_page, direction=direction)
        
        return self.current_index, self.index_of(to_page)

    def _direct_jump(self, to):
        """
        Bypasses the normal movement system and permissions for a
        direct jump to the given page. Used, e.g. when an experiment is
        aborted.
        """
        to_page = self.find_page(query=to)
        self.log.debug(f"Direct jump to {to_page}. Skipping all normal move function.")
        if self.exp.config.getboolean("data", "record_move_history"):
                self.record_move(self.current_page.is_closed, direction="jump", to_page=to_page)
         
        self.current_index = self.index_of(to_page)

    def _move(self, to_page, direction: str) -> Tuple[int, int]:
        try:
            return self._conduct_movement(to_page=to_page, direction=direction)
        except AbortMove:
            return self._abort_move()
    
    def forward(self):
        to_page = self.next_page
        self.previous_index, self.current_index = self._move(to_page, "forward")
    
    def backward(self):
        to_page = self.page_before(self.current_page)
        self.previous_index, self.current_index = self._move(to_page, "backward")
    
    def _check_jump_permission(self, next_page):
        if self.experiment.config.getboolean("general", "debug"):
            self.log.debug("Debug mode enabled. Jump permission not checked.")
            self.experiment.message_manager.post_message("Debug mode enabled. Jump permission was not checked.", level="debug")
            return True

        elif not self.current_page is next_page and not self.current_page.section.allow_jumpfrom:
            self.log.debug(f"The section of page {self.current_page} cannot be jumped from. Aborting move.")
            msg = self.experiment.config.get("hints", "jumpfrom_forbidden")
            self.experiment.message_manager.post_message(msg, level="warning")
            return False

        elif not next_page.section.allow_jumpto:
            msg = self.experiment.config.get("hints", "jumpto_forbidden")
            self.log.debug(f"The section of page {next_page} cannot be jumped to. Aborting move.")
            self.experiment.message_manager.post_message(msg, level="warning")
            return False

        else:
            return True
    
    def jump(self, to: Union[str, int]):
        to_page = self.find_page(query=to)
        
        if not to_page:
            msg = self.experiment.config.get("hints", "jump_page_not_found")
            self.experiment.message_manager.post_message(msg, level="warning")
            return False
        
        self.previous_index, self.current_index = self._move(to_page=to_page, direction="jump")

    def record_move(self, page_was_closed: bool, direction: str, to_page):
        current_page = self.current_page
        
        move = Move()
        move.exp_title = self.exp.title
        move.exp_author = self.exp.author
        move.exp_version = self.exp.config.get("metadata", "version")
        move.exp_id = self.exp.exp_id
        move.exp_session_id = self.exp.session_id
        move.move_number = len(self.history) + 1
        move.tree = current_page.short_tree
        move.page_name = current_page.name
        move.page_status_before_visit = "closed" if page_was_closed else "open"
        move.page_status_after_visit = "closed" if current_page.is_closed else "open"
        move.show_time = current_page.show_times[-1]
        
        try:
            move.hide_time = current_page.hide_times[-1]
            move.duration = move.hide_time - move.show_time
        except IndexError:
            self.log.debug(f"Hide time for {current_page} not available. This may be normal for an abort page.")
            move.hide_time = None
            move.duration = None
        
        move.previous_page = self.previous_page.name if self.previous_page else None
        move.section_allows_forward = current_page.section.allow_forward
        move.section_allows_backward = current_page.section.allow_backward
        move.section_allows_jumpfrom = current_page.section.allow_jumpfrom
        move.section_allows_jumpto = current_page.section.allow_jumpto
        move.leave_in_direction = direction
        move.target_page = to_page.name
        self.history.append(move)

    def move(self, direction, to: Union[str, int] = None):

        if self.exp.session_expired:
            return self.exp.abort(
                reason="session timed out", 
                title="Session expired",
                icon="hourglass-end",
                msg= "Sorry! The experiment session timed out."
                )
        
        proceed = self.current_page.custom_move()
        now = time.time()
        try:
            self.current_page._on_hiding_widget(hide_time=now)
        except AbortMove:
            return
        
        if not proceed:
            self.log.debug(f"Page defined its own move method. Alfred's move system stands by.")
            return
        
        if self.exp.aborted:
            self.log.debug(f"A move was called, but the experiment is aborted. No move is being conducted.")
            return
        
        if direction == "stay":
            self.log.debug("Movement direction was 'stay' - no move conducted.")
            return
        elif direction == "forward":
            self.forward()
        elif direction == "backward":
            self.backward()
        elif direction == "jump":
            self.jump(to=to)
        elif direction.startswith("jump"):
            self.jump(to=direction[5:]) # jump string has the form 'jump>pagename'
    
    def start(self):

        self.current_index = self.index_of(self.first_visible_page)
        self.exp.root_section._enter()
        self.current_page._on_showing_widget(show_time=time.time())


class UserInterface:
    instance_log = False

    _css_files = [
        "bootstrap-4.5.3.min.css",
        "prism.css",
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
        self._callables["set_page_data"] = self._set_page_data

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

    def _set_page_data(self, **data):
        data.pop("page_token", None)
        self.exp.current_page._set_data(data)
        self.log.info("Page data set via 'set_page_data' callable route.")
        self.exp.current_page.save_data()

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
                self.css_urls.append((5, url))
            
            self.config["logo_text"] = self.experiment.config.get("layout_base", "logo_text")
            logo = self.exp.subpath(self.exp.config.get("layout_goe", "logo"))
            if logo.is_file():
                self.config["logo_url"] = self.add_static_file(logo, content_type="image/png")

        elif style == "goe":

            with importlib.resources.path(css, "goe.css") as f:
                url = self.add_static_file(f, content_type="text/css")
                self.css_urls.append((5, url))

            with importlib.resources.path(img, "uni_goe_logo_white.png") as p:
                url = self.add_static_file(p, content_type="image/png")
                self.config["logo_url"] = url
            
            self.config["logo_text"] = self.experiment.config.get("layout_goe", "logo_text")

            logo = self.exp.subpath(self.exp.config.get("layout_goe", "logo"))
            if logo.is_file():
                self.config["logo_url"] = self.add_static_file(logo, content_type="image/png")
        else:
            raise ValueError(f"Invalid value for option 'style' in config section 'layout': {style}")
        
        # read CSS files from static folder
        static_folder = self.exp.config.get("layout", "static_folder")
        static_folder = self.exp.subpath(static_folder)
        try:
            for filename in static_folder.iterdir():
                if filename.is_file() and filename.suffix == ".css":
                    path = filename.resolve()
                    url = self.add_static_file(path, content_type="text/css")
                    self.css_urls.append((7, url))
        except FileNotFoundError:
            self.log.debug(f"Did not find static folder {static_folder}. Passing silently.")

        # read custom logo
        logo = self.experiment.config.get("layout", "logo")
        logo = self.experiment.subpath(logo)
        if logo.is_file():
            if logo.suffix == ".png":
                content_type = "image/png"
            elif logo.suffix in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            logo_url = self.add_static_file(logo, content_type=content_type)
            self.config["logo_url"] = logo_url

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

        self.experiment.data_manager.client_data.update(data)
        self.experiment.movement_manager.current_page.save_data()

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

        code["css_urls"] = page._css_urls
        code["css_code"] = page._css_code
        code["js_urls"] = page._js_urls
        code["js_code"] = page._js_code

        # JS Code for a single data saving call upon a visit to the first page
        # This is necessary in order to also save the screen resolution
        first_page = self.exp.movement_manager.first_visible_page
        if page is first_page and self.experiment.config.getboolean("data", "save_client_info"):
            code["js_code"] += [(7, importlib.resources.read_text(js, "clientinfo.js"))]
        
        try:
            code["css_code"] += self.exp.progress_bar.css_code
            code["js_code"] += self.exp.progress_bar.js_code
        except AttributeError:
            pass

        return code

    def render(self, page_token):
        """Renders the current page."""

        page = self.experiment.movement_manager.current_page
        d = {**self.config}
        
        if self.exp.config.getboolean("general", "debug") and not page is self.exp.final_page:
            d["debug"] = self.exp.config.getboolean("general", "debug")
            d["jumplist"] = page.elements[page.name + "__debug_jumplist__"]
        
        page.prepare_web_widget()

        d["code"] = self.code(page=page)
        d["page_token"] = page_token
        d["elements"] = page.elements.values()

        d["title"] = page.title
        d["subtitle"] = page.subtitle
        
        if not page is self.exp.movement_manager.first_page:
            previous_section = self.exp.movement_manager.page_before(page).section
            if previous_section.allow_backward and page.section.allow_backward:
                d["backward_text"] = self.experiment.config.get("navigation", "backward")
        
        if page.section.allow_forward:
            if self.exp.movement_manager.next_page is self.exp.root_section.final_page:
                d["finish_text"] = self.experiment.config.get("navigation", "finish")
            else:
                d["forward_text"] = self.experiment.config.get("navigation", "forward")

        messages = self.experiment.message_manager.get_messages()
        if messages:
            d["messages"] = messages

        # progress bar
        d["show_progress"] = self.experiment.config.getboolean("layout", "show_progress")
        d["fix_progress_top"] = self.experiment.config.getboolean("layout", "fix_progress_top")
        if d["show_progress"]:
            self.exp.progress_bar._prepare_web_widget()
            d["progress"] = self.exp.progress_bar.web_widget

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

        path = Path(path)
        if not path.is_absolute():
            path = self.experiment.path / path
        
        if self.experiment.config.getboolean("general", "debug"):
            identifier = str(path.name)
        else:
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
        self.exp.movement_manager.start()

