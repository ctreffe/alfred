# -*- coding:utf-8 -*-

"""
This module contains alfred's page classes.

Pages hold and organize elements. They receive, validate, and save 
data.


* Filling pages

    + linear style

    + object-oriented style

* Accessing element. You can access the elements of a page by using 
    dict-style square brackets and a number of specialized properties 
    listed below.

* Types of pages

* Custom layout for individual pages



.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>, Johannes Brachem <jbrachem@posteo.de>
"""
from __future__ import absolute_import

import time
import logging
import string
from abc import ABCMeta, abstractproperty, abstractmethod, ABC
from builtins import object, str
from functools import reduce
from pathlib import Path
from typing import Union
from typing import Iterator

from future.utils import with_metaclass

from . import alfredlog
from . import element as elm
from . import saving_agent
from ._core import ExpMember
from ._helper import _DictObj
from .exceptions import AlfredError


class PageCore(ExpMember):
    def __init__(
        self, minimum_display_time=0, minimum_display_time_msg=None, values: dict = {}, **kwargs,
    ):
        self._minimum_display_time = minimum_display_time
        self._minimum_display_time_msg = minimum_display_time_msg

        self._data = {}
        self._is_closed = False
        self._show_corrective_hints = False
        self.show_times = []
        self.hide_times = []

        super(PageCore, self).__init__(**kwargs)

        if not isinstance(values, dict):
            raise TypeError("The parameter 'values' requires a dictionary as input.")
        self.values = _DictObj(values)

    def added_to_experiment(self, experiment):

        if not isinstance(self, WebPageInterface):
            raise TypeError(f"{self} must be an instance of WebPageInterface.")

        super(PageCore, self).added_to_experiment(experiment)
        self.log.add_queue_logger(self, __name__)

        debug = self.experiment.config.getboolean("general", "debug")
        if debug and not self._minimum_display_time == 0:
            if self.experiment.config.getboolean("debug", "disable_minimum_display_time"):
                self.log.debug("Minimum display time disabled (debug mode).")
                self._minimum_display_time = 0

    @property
    def minimum_display_time_msg(self):
        msg = self._minimum_display_time_msg
        if msg is not None:
            return msg
        else:
            return self.experiment.config.get("messages", "minimum_display_time")

        try:
            self.experiment.page_controller.add_page(self)
        except AttributeError:
            if self.parent.tag == "finishedSection":
                pass

    @property
    def show_thumbnail(self):
        return True

    @property
    def show_corrective_hints(self):
        return self._show_corrective_hints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        self._show_corrective_hints = bool(b)

    @property
    def is_closed(self):
        return self._is_closed

    @property
    def should_be_shown(self) -> bool:
        """
        bool: Boolean, indicating whether a page should be shown.

        Evaluates the page's own settings, as well as the status of all
        of its parent sections. The page is only shown, if all 
        conditions evaluate to *True*.

        """
        thispage = super().should_be_shown
        sections = [sec.should_be_shown for sec in self.uptree()]
        return thispage and all(sections)
    
    @should_be_shown.setter
    def should_be_shown(self, value: bool):
        self._should_be_shown = bool(value)

    @property
    def has_been_shown(self) -> bool:
        return self._has_been_shown

    def _on_showing_widget(self, show_time: float = None):
        """
        Method for internal processes on showing Widget

        Args:
            show_time: Time of showing in seconds since epoch.
        """
        if show_time is None:
            show_time = time.time()
        self.show_times.append(show_time)

        if not self._has_been_shown:
            self.on_first_show()
            
            if self.exp.config.getboolean("general", "debug") and self is not self.exp.final_page:
                name = self.name + "__debug_jumplist__"
                jumplist = elm.JumpList(
                    scope="exp", 
                    check_jumpto=False, 
                    check_jumpfrom=False, 
                    name=name, 
                    debugmode=True
                    )
                jumplist.should_be_shown = False
                self += jumplist
            
        self.on_showing_widget()
        self.on_showing()
        self.on_each_show()

        self._has_been_shown = True

    def on_showing_widget(self):
        """**DEPRECATED**: Hook for code that is meant to be executed 
        *every time* the page is shown.
        
        .. note::
            **Note**: on_showing_widget is deprecated and will be 
            removed in future releases. Please use one of the 
            replacements:

            - on_first_show
            - on_each_show
        """
        pass

    def on_showing(self):
        """**DEPRECATED**: Hook for code that is meant to be executed 
        *every time* the page is shown.

        .. note::
            **Note**: on_showing is deprecated and will be removed in
            future releases. Please use one of the replacements:

            - on_first_show
            - on_each_show
        """
        pass

    def on_first_show(self):
        """Hook for code that is meant to be executed when a page is
        shown for the first time.

        This is your go-to-hook, if you want to have access to data 
        from other pages within the experiment, and your code is meant
        to be executed only once (i.e. the first time a page is shown).

        *New in v1.4.*
        """
        pass

    def on_each_show(self):
        """Hook for code that is meant to be executed *every time* the 
        page is shown.

        *New in v1.4.*
        """
        pass

    def _on_hiding_widget(self, hide_time: float = None):
        """
        Method for internal processes on hiding Widget

        Args:
            hide_time: Time of hiding in seconds since epoch.
        """
        if hide_time is None:
            hide_time = time.time()
        
        self.hide_times.append(hide_time)

        if not self._has_been_hidden:
            self.on_first_hide()

        self.on_hiding_widget()
        self.on_hiding()
        self.on_each_hide()

        self._has_been_hidden = True

        self.save_data()

    def on_hiding_widget(self):
        """**DEPRECATED**: Hook for code that is meant to be executed 
        *every time* the page is hidden.

        .. note::
            **Note**: on_hiding_widget is deprecated and will be removed
            in future releases. Please use one of the replacements:

            - on_first_hide
            - on_each_hide
            - on_close
        """
        pass

    def on_hiding(self):
        """**DEPRECATED**: Hook for code that is meant to be executed 
        *every time* the page is hidden.

        .. note::
            **Note**: on_hiding is deprecated and will be removed in
            future releases. Please use one of the replacements:

            - on_first_hide
            - on_each_hide
            - on_close
        """
        pass

    def on_first_hide(self):
        """Hook for code that is meant to be executed only once, when
        the page is hidden for the first time, **before** saving the
        page's data.

        .. note: **Important**: Note the difference to :meth:`on_close`, which is
        executed upon final submission of the page's data. When using
        :meth:`on_first_hide`, subject input can change (e.g., when a
        subject revists a page and changes his/her input).

        *New in v1.4.*
        """
        pass

    def on_each_hide(self):
        """Hook for code that is meant to be executed *every time* 
        the page is hidden, **before** saving the page's data.

        *New in v1.4*
        """
        pass

    def on_close(self):
        """Hook for code that is meant to be executed when a page is 
        closed, **before** saving the page's data.

        This is your go-to-hook, if you want to have the page execute 
        this code only once, when submitting the data from a page. After
        a page is closed, there can be no more changes to subject input.
        This is the most important difference of :meth:`on_close` from
        :meth:`on_first_hide` and :meth`on_each_hide`.

        *New in v1.4*
        """
        pass

    def on_exp_access(self):
        """Hook for code that is meant to be executed as soon as a page 
        is added to an experiment.
        
        This is your go-to-hook, if you want to have access to the 
        experiment, but don't need access to data from other pages.

        .. note::
            Compared to :meth:`on_first_show`, this method gets executed
            earlier, i.e. during experiment generation, while 
            :meth:`on_first_show` is executed on runtime.
        
        .. note::
            Internally, the hook is executed at the end of the 
            :class:`CoreCompositePage`'s added_to_experiment method,
            not the :class:`PageCore`'s.

        *New in v1.4*
        """
        pass

    def close_page(self):
        if not self.allow_closing:
            raise AlfredError()

        self.on_close()
        self._is_closed = True

    @property
    def allow_closing(self):
        return True

    def can_display_corrective_hints_in_line(self):
        return False

    def corrective_hints(self):
        """
        returns a list of corrective hints

        :rtype: list of unicode strings
        """
        return []

    def validate(self):
        """Alias for 'allow_leaving'. Better description of what this
        method does.
        """

        return self.allow_leaving()

    def allow_leaving(self):
        if not self.allow_closing:
            self.show_corrective_hints = True
            return False

        # check minimum display time
        mintime = self._minimum_display_time
        if time.time() - self.show_times[0] < mintime:
            msg = self.minimum_display_time_msg.replace("${mdt}", str(mintime))
            self.exp.message_manager.post_message(msg)
            return False

        return True

    def save_data(self, level: int = 1, sync: bool = False):
        """Saves current experiment data.
        
        Collects the current experimental data and calls the 
        experiment's main SavingAgentController to save the data with
        all SavingAgents.

        Args: 
            level: Level of the saving task. High level means high 
                importance. If the level is below a SavingAgent's 
                activation level, that agent will not be used for 
                processing this task. Defaults to 1.
            sync: If True, the saving task will be prioritised and the
                experiment will pause until the task was fully completed.
                Should be used carefully. Defaults to False.
        """
        if not self.exp.data_saver.main.agents and not self.exp.config.getboolean(
            "general", "debug"
        ):
            self.log.warning("No saving agents available.")
        data = self.experiment.data_manager.session_data
        self.exp.data_saver.main.save_with_all_agents(data=data, level=level, sync=sync)

    def __repr__(self):
        return f"Page(class='{type(self).__name__}', name='{self.name}')"

    def __str__(self):
        """*New in v1.4.*"""
        title = self.title if self.title is not None else "<None>"
        tag = self.tag if self.tag is not None else "<None>"
        return f"<Page of class '{type(self).__name__}', title: '{title}', tag: '{tag}', uid: '{self.uid}'>"


class WebPageInterface(with_metaclass(ABCMeta, object)):
    def prepare_web_widget(self):
        """Wird aufgerufen bevor das die Frage angezeigt wird, wobei jedoch noch
        Nutzereingaben zwischen aufruf dieser funktion und dem anzeigen der
        Frage kmmen koennen. Hier sollte die Frage, von
        noch nicht gemachten user Eingaben unabhaengige und rechenintensive
        verbereitungen fuer das anzeigen des widgets aufrufen. z.B. generieren
        von grafiken"""
        pass

    @property
    def web_thumbnail(self):
        return None

    @property
    def css_code(self):
        return []

    @property
    def css_urls(self):
        return []

    @property
    def js_code(self):
        return []

    @property
    def js_urls(self):
        return []

    def set_data(self, dictionary):
        pass


class CoreCompositePage(PageCore):
    def __init__(self, elements=None, **kwargs):
        super(CoreCompositePage, self).__init__(**kwargs)

        self.elements = {}

        self._element_list = []
        self._element_dict = {}
        self._element_name_counter = 1
        self._thumbnail_element = None
        
        if elements is not None:
            if not isinstance(elements, list):
                raise TypeError
            self.append(*elements)
    
    def __contains__(self, element): 
        try:
            return element.name in self.elements
        except AttributeError:
            return element in self.elements
    
    # necessary to make __getattr__ work with copying a page object
    def __getstate__(self): return self.__dict__

    # necessary to make __getattr__ work with copying a page object
    def __setstate__(self, state): self.__dict__.update(state) 

    def __getitem__(self, name): return self.elements[name]
    
    def __getattr__(self, name):
        try:
            return self.elements[name]
        except KeyError:
            raise AttributeError(f"{self} has no attribute '{name}'.")
    
    @property
    def input_elements(self) -> dict:
        """Dict of all input elements on this page.

        Does not evaluate whether an input element should be shown or
        not, because that might change over the course of an experiment.
        """

        input_elements = {}
        for name, el in self.elements.items():
            if isinstance(el, (elm.InputElement)):
                input_elements[name] = el
        return input_elements
    
    @property
    def all_input_elements(self) -> dict:
        return self.input_elements
    
    @property
    def all_elements(self) -> dict:
        return self.elements
    
    @property
    def updated_elements(self) -> dict:
        return {name: elm for name, elm in self.elements.items() if elm.exp is not None}

    @property
    def filled_input_elements(self) -> dict:
        """Dict of all input elements on this page with non-empty data attribute.
        """

        return {name: el for name, el in self.input_elements.items() if el.input}
    
    @property
    def all_parent_sections(self) -> dict:
        
        pass
    
    @property
    def element_dict(self):
        return self._element_dict

    def add_element(self, element):

        self.log.warning("page.add_element() is deprecated. Use page.append() instead.")

        self.append(element)

    def add_elements(self, *elements):
        self.log.warning("page.add_elements() is deprecated. Use page.append() instead.")

        for elmnt in elements:
            self.append(elmnt)

    def append(self, *elements):
        for elmnt in elements:
            if not isinstance(elmnt, (elm.Element)):
                raise TypeError(f"Can only append elements to pages, not '{type(elmnt).__name__}'")

            elmnt.added_to_page(self)
            
            if elmnt.name in dir(self):
                raise ValueError(f"Element name '{elmnt.name}' is also an attribute of {self}.")

            if elmnt.name in self.elements:
                raise AlfredError(f"{self} already has an element of name '{elmnt.name}'.")


            if self.exp is not None and elmnt.exp is None:
                elmnt.added_to_experiment(self.exp)
            
            self.elements[elmnt.name] = elmnt
    
    def generate_element_name(self, element):
        i = self._element_name_counter
        c = element.__class__.__name__
        self._element_name_counter += 1

        return f"{self.name}_{c}_{i}"

    def __iadd__(self, other):
        self.append(other)
        return self

    @property
    def element_list(self):
        return self._element_list

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self.on_exp_access()
        self.update_elements()
    
    def added_to_section(self, section):
        super().added_to_section(section)
        self.update_elements()
    
    def update_members_recursively(self):
        self.update_elements()
    
    def update_elements(self):
        if self.exp and self.section and self.tree.startswith("_root"):
            for element in self.elements.values():
                if not element.exp:
                    element.added_to_experiment(self.experiment)

    @property
    def allow_closing(self):
        return all([el.validate_data() for el in self.input_elements.values()])

    def close(self):
        self.close_page()

    def close_page(self):
        super(CoreCompositePage, self).close_page()

        for elmnt in self.elements.values():
            if isinstance(elmnt, elm.InputElement):
                elmnt.disabled = True

        debug_jumplist = self.elements.get(self.name + "__debug_jumplist__")
        if debug_jumplist:
            for elmnt in debug_jumplist.elements:
                elmnt.disabled = False

    @property
    def data(self):
        if not self.has_been_shown:
            return {}
        else:
            data = {}
            for element in self.input_elements.values():
                data.update(element.data)
            return data

    @property
    def unlinked_data(self):
        return {}
    
    def set_data(self, dictionary):
        for elmnt in self.input_elements.values():
            elmnt.set_data(dictionary)

    def custom_move(self):
        """
        Hook for defining a page's own movement behavior. 
        
        Use the :class:`.MovementManager`s movement methods to define
        your own behavior. The available methods are

        - forward
        - backward
        - jump_by_name
        - jump_by_index

        Example::

            exp = al.Experiment()

            @exp.member
            class CustomMove(al.Page):
                name = "custom_move"
                
                def custom_move(self):
                    self.exp.jump(to="third")

            exp += al.Page(name="second")
            exp += al.Page(name="third")


        You can work with different conditions and fall back to 
        alfred3's movement system by returning *True*::
            
            exp = al.Experiment()

            @exp.member
            class CustomMove(al.Page):

                def on_exp_access(self):
                    self += elm.TextEntry(name="text")
                
                def custom_move(self):
                    if self.data.get("text) == "yes":
                        self.exp.jump(to="third")
                    else:
                        return True

            exp += al.Page(name="second")
            exp += al.Page(name="third")
        
        """
        return True

    def durations(self) -> Iterator[float]:
        """
        Iterates over the visit durations for this page.

        Yields:
            float: Duration of a visit in seconds.
        """
        
        if len(self.show_times) > len(self.hide_times):
            now = time.time()
        elif len(self.show_times) < len(self.hide_times):
            self.log.error(f"{self} has fewer entries in show_times than in hide_times.")
        
        for show, hide in zip(self.show_times, self.hide_times + [now]):
            yield hide - show
    
    def last_duration(self) -> float:

        *_, last_duration = self.duration()
        return last_duration
    
    def first_duration(self) -> float:

        first_duration, *_ = self.durations()
        return first_duration


class WebCompositePage(CoreCompositePage, WebPageInterface):
    def __init__(self, title: str = None, name: str = None, *args, **kwargs):
        super().__init__(title=title, name=name, *args, **kwargs)

        self._fixed_width = None
        if kwargs.get("fixed_width"):
            self.fixed_width = kwargs.get("fixed_width")

        self._responsive_width = None
        if kwargs.get("responsive_width"):
            self.responsive_width = kwargs.get("responsive_width")

        self._header_color = None
        if kwargs.get("header_color"):
            self.header_color = kwargs.get("header_color")

        self._background_color = None
        if kwargs.get("background_color"):
            self.background_color = kwargs.get("background_color")

    @property
    def fixed_width(self):
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, value):
        self._fixed_width = value

    @property
    def responsive_width(self):
        return self._responsive_width

    @responsive_width.setter
    def responsive_width(self, value):
        self._responsive_width = value

    @property
    def header_color(self):
        return self._header_color

    @header_color.setter
    def header_color(self, value):
        self._header_color = value

    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, value):
        self._background_color = value

    def _parse_responsive_width(self, width):
        return [x.strip() for x in width.split(",")]

    def _responsive_media_query(self, width):
        if len(width) > 4:
            raise ValueError("The option 'responsive_width' can only define up to four widths.")

        if len(width) < 4:
            for _ in range(4 - len(width)):
                width.append(width[-1])

        screen_size = [576, 768, 992, 1200]
        t = string.Template(
            "@media (min-width: ${screen}px) {.responsive-width { width: ${w}%; max-width: none;}}"
        )
        out = []
        for i, w in enumerate(width):
            out.append(t.substitute(screen=screen_size[i], w=w))
        return " ".join(out)

    def prepare_web_widget(self):
        for elmnt in self.elements.values():
            elmnt._prepare_web_widget()

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self._set_width()
        self._set_color()

    def _set_width(self):
        if self.experiment.config.getboolean("layout", "responsive"):

            if self.responsive_width:
                w = self._parse_responsive_width(self.responsive_width)
                self += elm.Style(code=self._responsive_media_query(w))

            elif self.experiment.config.get("layout", "responsive_width"):
                config_width = self.experiment.config.get("layout", "responsive_width")
                w = self._parse_responsive_width(config_width)
                self += elm.Style(code=self._responsive_media_query(w))

        elif not self.fixed_width:
            w = self.experiment.config.get("layout", "fixed_width")
            self += elm.Style(code=f".fixed-width {{ width: {w}; }}")
            self += elm.Style(code=f".min-width {{ min-width: {w}; }}")

        else:
            self += elm.Style(code=f".fixed-width {{ width: {self.fixed_width}; }}")
            self += elm.Style(code=f".min-width {{ min-width: {self.fixed_width}; }}")

    def _set_color(self):
        if self.header_color:
            self += elm.Style(code=f".logo-bg {{background-color: {self.header_color};}}")

        elif self.experiment.config.get("layout", "header_color", fallback=False):
            c = self.experiment.config.get("layout", "header_color", fallback=False)
            self += elm.Style(code=f".logo-bg {{background-color: {c};}}")

        if self.background_color:
            self += elm.Style(code=f"body {{background-color: {self.background_color};}}")

        elif self.experiment.config.get("layout", "background_color", fallback=False):
            c = self.experiment.config.get("layout", "background_color", fallback=False)
            self += elm.Style(code=f"body {{background-color: {c};}}")

    @property
    def web_thumbnail(self):
        """
        gibt das thumbnail von self._thumbnail_element oder falls self._thumbnail_element nicht gesetzt, das erste thumbnail eines elements aus self._element_list zurueck.

        .. todo:: was ist im fall, wenn thumbnail element nicht gestzt ist? anders verhalten als jetzt???

        """
        if not self.show_thumbnail:
            return None

        if self._thumbnail_element:
            return self._thumbnail_element.web_thumbnail
        else:
            for elmnt in self._element_list:
                if elmnt.web_thumbnail and elmnt.should_be_shown:
                    return elmnt.web_thumbnail
            return None

    @property
    def css_code(self):
        return reduce(lambda l, element: l + element.css_code, self.elements.values(), [])

    @property
    def css_urls(self):
        return reduce(lambda l, element: l + element.css_urls, self.elements.values(), [])

    @property
    def js_code(self):
        return reduce(lambda l, element: l + element.js_code, self.elements.values(), [])

    @property
    def js_urls(self):
        return reduce(lambda l, element: l + element.js_urls, self.elements.values(), [])


class CompositePage(WebCompositePage):
    pass


class Page(WebCompositePage):
    pass


class WidePage(Page):
    responsive_width = "85, 75, 75, 70"


class PagePlaceholder(PageCore, WebPageInterface):
    def __init__(self, ext_data={}, **kwargs):
        super(PagePlaceholder, self).__init__(**kwargs)

        self._ext_data = ext_data

    @property
    def web_widget(self):
        return ""

    @property
    def data(self):
        data = {}
        data.update(self._ext_data)
        return data

    @property
    def should_be_shown(self):
        return False

    @should_be_shown.setter
    def should_be_shown(self, b):
        pass

    @property
    def is_jumpable(self):
        return False

    @is_jumpable.setter
    def is_jumpable(self, is_jumpable):
        pass


class AutoHidePage(CompositePage):
    def __init__(self, on_hiding=False, on_closing=True, **kwargs):
        super(AutoHidePage, self).__init__(**kwargs)

        self._on_closing = on_closing
        self._on_hiding = on_hiding

    def on_hiding_widget(self):
        if self._on_hiding:
            self.should_be_shown = False

    def close_page(self):
        super(AutoHidePage, self).close_page()
        if self._on_closing:
            self.should_be_shown = False


class NoNavigationPage(Page):
    """A normal page, but all navigation buttons are removed."""

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self += elm.Style("#page-navigation {display: none;}")


####################
# Page Mixins
####################


class WebTimeoutMixin(object):
    def __init__(self, timeout, **kwargs):
        super(WebTimeoutMixin, self).__init__(**kwargs)

        self._end_link = "unset"
        self._run_timeout = True
        self._timeout = timeout

    def added_to_experiment(self, experiment):
        super(WebTimeoutMixin, self).added_to_experiment(experiment)
        self._end_link = self._experiment.user_interface_controller.add_callable(self.callback)

        if self._experiment.config.getboolean("general", "debug"):
            if self._experiment.config.getboolean("debug", "reduce_countdown"):
                self._timeout = self._experiment.config.getint("debug", "reduced_countdown_time")

    def callback(self, *args, **kwargs):
        self._run_timeout = False
        self._experiment.user_interface_controller.update_with_user_input(kwargs)
        return self.on_timeout(*args, **kwargs)

    def on_hiding_widget(self):
        self._run_timeout = False
        super(WebTimeoutMixin, self).on_hiding_widget()

    def on_timeout(self, *args, **kwargs):
        pass

    @property
    def js_code(self):
        code = (
            5,
            """
            $(document).ready(function(){
                var start_time = new Date();
                var timeout = %s;
                var action_url = '%s';

                var update_counter = function() {
                    var now = new Date();
                    var time_left = timeout - Math.floor((now - start_time) / 1000);
                    if (time_left < 0) {
                        time_left = 0;
                    }
                    $(".timeout-label").html(time_left);
                    if (time_left > 0) {
                        setTimeout(update_counter, 200);
                    }
                };
                update_counter();

                var timeout_function = function() {
                    $("#form").attr("action", action_url);
                    $("#form").submit();
                };
                setTimeout(timeout_function, timeout*1000);
            });
        """
            % (self._timeout, self._end_link),
        )
        js_code = super(WebTimeoutMixin, self).js_code
        if self._run_timeout:
            js_code.append(code)
        else:
            js_code.append((5, """$(document).ready(function(){$(".timeout-label").html(0);});"""))
        return js_code


class WebTimeoutForwardMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self.experiment.movement_manager.forward()


class WebTimeoutCloseMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self.close_page()


class HideButtonsMixin(object):
    def _on_showing_widget(self):
        self._experiment.user_interface_controller.layout.forward_enabled = False
        self._experiment.user_interface_controller.layout.backward_enabled = False
        self._experiment.user_interface_controller.layout.jump_list_enabled = False
        self._experiment.user_interface_controller.layout.finish_disabled = True

        super(HideButtonsMixin, self)._on_showing_widget()

    def _on_hiding_widget(self):
        self._experiment.user_interface_controller.layout.forward_enabled = True
        self._experiment.user_interface_controller.layout.backward_enabled = True
        self._experiment.user_interface_controller.layout.jump_list_enabled = True
        self._experiment.user_interface_controller.layout.finish_disabled = False

        super(HideButtonsMixin, self)._on_hiding_widget()


####################
# Pages with Mixins
####################


class WebTimeoutForwardPage(WebTimeoutForwardMixin, WebCompositePage):
    pass


class WebTimeoutClosePage(WebTimeoutCloseMixin, WebCompositePage):
    pass

class TimeoutForwardPage(WebTimeoutForwardPage): pass

class TimeoutClosePage(WebTimeoutClosePage): pass

class NoDataPage(Page):
    """This Page does not save any data except its tag and uid."""

    data = {}


class UnlinkedDataPage(NoDataPage):
    """This Page saves unlinked data.

    Unlinked data is data that does not contain any identifiers that
    would allow someone to establish a connection between an 
    experiment data set and the unlinked data set. 
    A common use case is the sepration of identifying personal 
    information that might be needed for non-experimental purposes such 
    as compensation admninistration, from experiment data.

    In practice that means that the UnlinkedDataPage does not save any
    of the following:

    - Time of saving
    - Session ID
    - Experiment condition
    - Additional data
    - Start time
    - Experiment version
    - Alfred version

    It will, however, save the following information:

    - Experiment Title
    - Experiment ID
    - Experiment Author
    - Page tag
    - Page ID

    Thus, the saved data *can* be linked to an *experiment* and to a
    page. That is intended and indeed necessary so that data 
    can be retrieved and processed. The key point is that there is no
    identifier for linking data to data from a specific experimental 
    *session* (i.e. the name of a subject, saved with an 
    UnlinkedDataPage cannot be linked to his/her answers given on other
    Pages).

    Args:
        encrypt: Takes one the following values: 'agent' (default) will
            encrypt data based on each saving agent's configuration.
            'always' will encrypt all data entered on this page, 
            regardless of saving agent configuration. 'never' will turn
            off encryption for this page, regardless of saving agent
            configuration.

    .. warning::
        All data from UnlinkedDataPages is saved in a single unlinked 
        data document, so data from two different unlinked pages *are* 
        linked to each other (though not to the rest of the experiment
        data).

    """

    def __init__(self, encrypt: str = "agent", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encrypt = encrypt

        if self.encrypt not in ["agent", "always", "never"]:
            raise ValueError(
                "The argument 'encrypt' must take one of the following values: 'agent', 'always', 'never'."
            )
    
    @property
    def unlinked_data(self):
        if not self.has_been_shown:
            return {}
        else:
            data = {}
            for element in self.input_elements.values():
                data.update(element.data)
            return data
    
    def save_data(self, level: int = 1, sync: bool = False):
        """Saves current unlinked data.
        
        Collects the unlinked data from all UnlinkedDataPages in the
        experiment and engages the experiment's unlinked
        SavingAgentController to save the data with all SavingAgents.

        Args: 
            level: Level of the saving task. High level means high 
                importance. If the level is below a SavingAgent's 
                activation level, that agent will not be used for 
                processing this task. Defaults to 1.
            sync: If True, the saving task will be prioritised and the
                experiment will pause until the task was fully completed.
                Should be used carefully. Defaults to False.
        """
        if (
            not self._experiment.data_saver.unlinked.agents
            and not self._experiment.config.getboolean("general", "debug")
        ):
            self.log.warning("No saving agent for unlinked data available.")

        for agent in self._experiment.data_saver.unlinked.agents.values():
            
            if self.encrypt == "agent":
                data = self.experiment.data_manager.unlinked_data_with(agent)
            elif self.encrypt == "always":
                data = self.experiment.data_manager.unlinked_data
                data = self.experiment.data_manager.encrypt_values(data)
            elif self.encrypt == "never":
                data = self.experiment.data_manager.unlinked_data

            self.exp.data_saver.unlinked.save_with_agent(
                data=data, name=agent.name, level=level, sync=sync
            )


class CustomSavingPage(Page, ABC):
    """Allows you to add custom SavingAgents directly to the page.

    Since this is an abstract class, it can not be instantiated directly.
    You have to derive a child class and define the property
    :meth:`custom_save_data`, which must return a dictionary. Through
    this property, you control exactly which data will be saved by this
    page.

    Example 1: Saving ordinary page data (like other pages)::

        class MyPage(CustomSavingPage):

            @property
            def custom_save_data(self):
                return self.data


    Example 2: Saving a static dictionary

        class MyPage(CustomSavingPage):

            @property
            def custom_save_data(self):
                return {"key": "value"}

    .. warning::
        Each SavingAgent maintains one file or one document. 
        On saving, the document will be fully replaced with the current
        data. That means, you should not let two CustomSavingPages
        share a SavingAgent, as they will override each other's data.
        That is, unless that is your intended behavior, e.g. when the
        pages share data.

    Args:
        experiment: Alfred experiment. This page must be initialized
            with an experiment.
        save_to_main: If True, data will be *also* saved using the
            experiment's main SavingAgentController and all of its
            SavingAgents. Defaults to False.
    """

    def __init__(self, experiment, save_to_main: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._experiment = experiment
        self.saving_agent_controller = saving_agent.SavingAgentController(self._experiment)
        self.save_to_main = save_to_main

    def added_to_experiment(self, experiment):
        if not self._experiment:
            super().added_to_experiment(experiment=experiment)
            self.saving_agent_controller = saving_agent.SavingAgentController(self._experiment)
        self._check_for_duplicate_agents()

    def _check_for_duplicate_agents(self):
        comparison = []
        comparison += list(self._experiment.data_saver.main.agents.values())
        comparison += list(self._experiment.data_saver.unlinked.agents.values())

        for pg in self._experiment.root_section.all_pages.values():
            if pg == self:
                continue
            try:
                comparison += list(pg.saving_agent_controller.agents.values())
            except AttributeError:
                pass

        for agent in self.saving_agent_controller.agents.values():
            self._check_one_duplicate(agent, comparison)

    @staticmethod
    def _check_one_duplicate(agent, agents_list):
        for ag in agents_list:
            if ag == agent:
                raise ValueError("A SavingAgent added to a CustomSavingPage must be unique")

    def append_saving_agents(self, *args):
        """Appends saving agents to this page.
        
        These saving agents will be used to save the page's data.
        """
        for agent in args:
            self.saving_agent_controller.append(agent)
        self._check_for_duplicate_agents()

    def append_failure_saving_agents(self, *args):
        for agent in args:
            self.saving_agent_controller.append_failure_agent(agent)

    @abstractproperty
    def custom_save_data(self):
        pass

    def save_data(self, level=1, sync=False):

        if not isinstance(self.custom_save_data, dict):
            raise ValueError("The porperty 'custom_page_data' must return a dictionary.")

        if self.save_to_main:
            self._experiment.data_saver.main.save_with_all_agents(level=level, sync=sync)

        self.saving_agent_controller.save_with_all_agents(
            data=self.custom_save_data, level=level, sync=sync
        )


class DefaultFinalPage(Page):
    title = "Experiment beendet"

    def on_exp_access(self):
        txt = "Das Experiment ist nun beendet.<br>Vielen Dank für die Teilnahme."
        self += elm.Text(text=txt, align="center")
        self += elm.WebExitEnabler()
