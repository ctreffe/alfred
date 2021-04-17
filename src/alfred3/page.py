# -*- coding:utf-8 -*-

"""
Pages hold and organize elements.

.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>, Johannes Brachem <jbrachem@posteo.de>
"""
import time
import logging
import string
from abc import ABCMeta, abstractproperty, abstractmethod, ABC
from builtins import object, str
from functools import reduce
from pathlib import Path
from typing import Union
from typing import Iterator

from . import alfredlog
from . import element as elm
from .element.misc import Style
from . import saving_agent
from ._core import ExpMember
from ._helper import _DictObj
from ._helper import inherit_kwargs
from .exceptions import AlfredError, ValidationError, AbortMove


@inherit_kwargs
class _PageCore(ExpMember):
    """
    Provides core functionality for pages.

    Args:
        prefix_element_names (bool): If True, the names of all input 
            elements on this page will be prefixed with the page name.
            Defaults to None. Can be defined as a class attribute.
        minimum_display_time (str): The minimal amount of time that the page
            must be displayed, before participants can move to the next
            page. Defaults to None. Can be defined as a class attribute.
        minimum_display_time_msg (str): A page-specific message to be displayed,
            if participants try to move forward before the minimum
            display time has expired. Defaults to None, which means that
            the default message defined in config.conf will be used.
            Can be defined as a class attribute.
        {kwargs}
    """

    #: If *True*, the names of all elements added to this page will
    #: receive a prefix of the page's name.
    prefix_element_names: bool = False

    def __init__(
        self,
        prefix_element_names: bool = None,
        minimum_display_time: str = None,
        minimum_display_time_msg: str = None,
        **kwargs,
    ):
        self._minimum_display_time = "0s"
        
        if minimum_display_time is not None:
            self.minimum_display_time = minimum_display_time

        if minimum_display_time_msg:
            self._minimum_display_time_msg = minimum_display_time_msg
        else:
            self._minimum_display_time_msg = None
        
        if prefix_element_names is not None:
            self.prefix_element_names = prefix_element_names

        self._data = {}
        self._is_closed = False
        self.show_times = []
        self.hide_times = []

        self.elements = {}

        self._element_name_counter = 1

        super().__init__(**kwargs)

    @property
    def elements(self):
        """
        Dictionary of elements belonging to this page.
        """
        return self._elements
    
    @elements.setter
    def elements(self, value):
        self._elements = value

    @property
    def minimum_display_time(self) -> str:
        """
        str: Minimal amount of time that a page must be displayed
        before participants can move forward.

        Must be specified as a string with a unit of 's' (for seconds),
        or 'm' (for minutes).
        """
        return self._minimum_display_time
    
    @property
    def _mdt(self) -> float:
        mdt = self.minimum_display_time
        unit = mdt[-1]
        if unit == "s":
            return float(mdt[:-1])
        elif unit == "m":
            return float(mdt[:-1]) * 60
        else:
            raise ValueError(
                "Please specify minimum display time with a unit ('s' - seconds, 'm' - minutes)."
            )

    @minimum_display_time.setter
    def minimum_display_time(self, value: str):
        self._minimum_display_time = value

    def added_to_experiment(self, experiment):
        # docstring inherited
        super().added_to_experiment(experiment)
        self.log.add_queue_logger(self, __name__)

        debug = self.experiment.config.getboolean("general", "debug")
        if debug and not self._mdt == 0:
            if self.experiment.config.getboolean("debug", "disable_minimum_display_time"):
                self.log.debug("Minimum display time disabled (debug mode).")
                self.minimum_display_time = "0s"

    @property
    def minimum_display_time_msg(self) -> str:
        """
        Message that is displayed if participants try to leave a page
        before the minimum display time is up.
        """
        msg = self._minimum_display_time_msg
        if msg is not None:
            return msg
        else:
            return self.experiment.config.get("hints", "minimum_display_time")

    @minimum_display_time_msg.setter
    def minimum_display_time_msg(self, value: str):
        self._minimum_display_time_msg = value

    @property
    def is_closed(self) -> bool:
        """
        Returns *True*, if the page is closed.
        """
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
    def must_be_shown(self) -> bool:
        """
        bool: False, if the experiment tolerates skipping this
        page entirely. Defaults to False.

        Notes:
            If there are input elements with *force_input=True* on a
            skippable page, particpants will be notified and validation
            will fail, even if the *must_be_shown* attribute of the page
            itself is set to False.

            If a page that must be shown has not been shown, the
            experiment will display the hint *page_must_be_shown* as defined
            in config.conf, section "hints".

            ..warning::
                It is easy to end up in a situation where
                a mandatory page has not been shown, but the participant has
                no way of moving back to it. So, please be careful when
                using this option.

        """
        return False

    @property
    def has_been_shown(self) -> bool:
        """
        Returns *True*, if the page has been displayed in the ongoing
        experiment session.
        """
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
                jumplist = elm.action.JumpList(
                    scope="exp",
                    check_jumpto=False,
                    check_jumpfrom=False,
                    name=name,
                    debugmode=True,
                )
                jumplist.should_be_shown = False
                self += jumplist

        self.on_each_show()

        self._has_been_shown = True
        if self.exp.aborted:
            raise AbortMove

    def on_first_show(self):
        """
        Executed *once*, when the page is shown for the first time,
        *before* executing :meth:`~.Page.on_each_show`.

        This is your go-to-hook, if you want to have access to data
        from other pages within the experiment, and your code is meant
        to be executed only once (i.e. the first time a page is shown).

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

        """
        pass

    def on_each_show(self):
        """
        Executed *every time* the page is shown, *after* executing
        :meth:`~.Page.on_first_show`.

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

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

        self.on_each_hide()

        self._has_been_hidden = True

        self.save_data()

        if self.exp.aborted:
            raise AbortMove

    def on_first_hide(self):
        """
        Executed *once*, when the page is hidden for the first time,
        *before* executing :meth:`~.Page.on_each_hide`.

        Hook for code that is meant to be executed only once, when
        the page is hidden for the first time, **before** saving the
        page's data.

        Notes:
            Note the difference to :meth:`on_close`, which is
            executed upon final submission of the page's data. When using
            :meth:`on_first_hide`, subject input can change (e.g., when a
            subject revists a page and changes his/her input).

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

        """
        pass

    def on_each_hide(self):
        """
        Executed *every time* the page is hidden, *before* closing it
        and *before* saving data, but *after* executing
        :meth:`~.Page.on_first_hide`.

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

        """
        pass

    def on_close(self):
        """
        Executed *once*, when the page is closed, *before* data saving.

        This is your go-to-hook, if you want to have the page execute
        this code only once, when submitting the data from a page. After
        a page is closed, there can be no more changes to subject input.
        This is the most important difference of :meth:`on_close` from
        :meth:`on_first_hide` and :meth`on_each_hide`.

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

        """
        pass

    def on_exp_access(self):
        """
        Executed *once*, when the :class:`.ExperimentSession` becomes
        available to the page.

        This is your go-to-hook, if you want to have access to the
        experiment, but don't need access to data from other pages.

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

        """
        pass

    def close(self):
        """
        Closes the page. Usually, sections will take care of closing
        pages. Only call this method, if you cannot solve your problem
        by using a certain section.
        """
        self.on_close()
        self._is_closed = True

    def validate_page(self) -> bool:
        """
        Returns *True*, if the validation checks pass, *False* otherwise.
        """
        return True

    def validate_elements(self) -> bool:
        """
        Returns *True*, if validation of all input elements passes,
        *False* otherwise.
        """
        return True

    def save_data(self, level: int = 1, sync: bool = False):
        """
        Saves current experiment data.

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

        Notes:
            Note that this function will be called automatically on every
            move in the experiment. Only call it yourself if it is 
            really necessary.
        """
        if not self.exp.data_saver.main.agents and not self.exp.config.getboolean(
            "general", "debug"
        ):
            self.log.warning("No saving agents available.")
        data = self.experiment.data_manager.session_data
        self.exp.data_saver.main.save_with_all_agents(data=data, level=level, sync=sync)

    def __repr__(self):
        return f"Page(class='{type(self).__name__}', name='{self.name}')"

    def prepare_web_widget(self):
        """
        Hook for computations for preparing a page for display.

        Gets executed *every time* before the page is displayed.
        """
        pass

    @property
    def _css_code(self):
        return []

    @property
    def _css_urls(self):
        return []

    @property
    def _js_code(self):
        return []

    @property
    def _js_urls(self):
        return []

    def _set_data(self, dictionary: dict):
        """
        Informs the page's input elements about user input.
        """
        pass


@inherit_kwargs
class _CoreCompositePage(_PageCore):
    """
    Second base class for pages.

    Args:
        {kwargs}
    """

    def __contains__(self, element):
        try:
            return element.name in self.elements
        except AttributeError:
            return element in self.elements

    # necessary to make __getattr__ work with copying a page object
    def __getstate__(self):
        return self.__dict__

    # necessary to make __getattr__ work with copying a page object
    def __setstate__(self, state):
        self.__dict__.update(state)

    def __getitem__(self, name):
        return self.elements[name]

    def __getattr__(self, name):
        try:
            return self.elements[name]
        except KeyError:
            raise AttributeError(f"{self} has no attribute '{name}'.")

    @property
    def input_elements(self) -> dict:
        """
        Dict of all input elements on this page.

        Does not evaluate whether an input element should be shown or
        not, because that might change over the course of an experiment.
        """

        input_elements = {}
        for name, el in self.elements.items():
            if isinstance(el, (elm.core.InputElement)):
                input_elements[name] = el
        return input_elements

    @property
    def all_input_elements(self) -> dict:
        """
        Alias for :attr:`.input_elements`.
        """
        return self.input_elements

    @property
    def all_elements(self) -> dict:
        """
        Alias for :attr:`.elements`.
        """
        return self.elements

    @property
    def updated_elements(self) -> dict:
        """
        Returns a dict of all elements on the page that already have 
        access to the experiment session.
        """
        return {name: elm for name, elm in self.elements.items() if elm.exp is not None}

    @property
    def filled_input_elements(self) -> dict:
        """
        Dict of all input elements on this page with non-empty data 
        attribute. This includes elements that hav received participant
        input and elements with default values.
        """

        return {name: el for name, el in self.input_elements.items() if el.input}

    def append(self, *elements):
        """
        Appends a variable number of elements to the page.

        In practice, it is recommended to use the augmented assignment
        operator ``+=`` instead in order to add elements.
        """
        for elmnt in elements:
            if not isinstance(elmnt, (elm.core.Element)):
                raise TypeError(f"Can only append elements to pages, not '{type(elmnt).__name__}'")

            elmnt.added_to_page(self)

            if elmnt.name in dir(self):
                raise ValueError(f"Element name '{elmnt.name}' is also an attribute of {self}.")

            if elmnt.name in self.elements:
                raise AlfredError(f"{self} already has an element of name '{elmnt.name}'.")

            if self.exp is not None and elmnt.exp is None:
                elmnt.added_to_experiment(self.exp)

            self.elements[elmnt.name] = elmnt

    def _generate_element_name(self, element):
        i = self._element_name_counter
        c = element.__class__.__name__
        self._element_name_counter += 1

        return f"{self.name}_{c}_{i}"

    def __iadd__(self, other):
        self.append(other)
        return self


    def added_to_experiment(self, experiment):
        # docstring inherited
        super().added_to_experiment(experiment)
        self.on_exp_access()
        self._update_elements()

    def added_to_section(self, section):
        # docstring inherited
        super().added_to_section(section)
        self._update_elements()

    def _update_members_recursively(self):
        self._update_elements()

    def _update_elements(self):
        if self.exp and self.section and self.tree.startswith("_root"):
            for element in self.elements.values():
                if not element.exp:
                    element.added_to_experiment(self.experiment)

    def close(self):
        # docstring inherited
        super().close()

        for elmnt in self.elements.values():
            if isinstance(elmnt, elm.core.InputElement):
                elmnt.disabled = True

        debug_jumplist = self.elements.get(self.name + "__debug_jumplist__")
        if debug_jumplist:
            for elmnt in debug_jumplist.elements:
                elmnt.disabled = False

    @property
    def data(self) -> dict:
        """
        Returns a dict of data for all input elements on the page. 

        If the page has not been shown yet, an empty dict is returned.
        """

        if not self.has_been_shown:
            return {}
        else:
            data = {}
            for element in self.input_elements.values():
                data.update(element.data)
            return data

    @property
    def unlinked_data(self) -> dict:
        """
        Returns an empty dict for 'normal' pages and the input data
        for unlinked pages.
        """
        return {}

    def _set_data(self, dictionary: dict):
        for elmnt in self.input_elements.values():
            elmnt.set_data(dictionary)

    def custom_move(self):
        """
        Hook for defining a page's own movement behavior, executed
        *every time* a movement *from* the page takes place,
        *before* :meth:`~.Page.on_first_hide` and :meth:`~.Page.on_each_hide`.

        User input to the elements on the current page is available in
        this method through the page's :attr:`.Page.data` attribute.

        Use the :class:`.ExperimentSession` s movement methods to define
        your own behavior. The available methods are

        .. autosummary::
           :nosignatures:

           ~alfred3.experiment.ExperimentSession.forward
           ~alfred3.experiment.ExperimentSession.backward
           ~alfred3.experiment.ExperimentSession.jump

        Notes:
            You can fall back to alfred3's movement system by returning
            *True* from your custom move function.

        Examples:

            Create a page that always jumps to a specific page upon
            submission::

                exp = al.Experiment()

                @exp.member
                class CustomMove(al.Page):
                    name = "custom_move"

                    def custom_move(self):
                        self.exp.jump(to="third")

                exp += al.Page(name="second")
                exp += al.Page(name="third")


            Create a page that jumps to a specific page, if it received
            a user input of 'yes', and use alfred3's usual movement
            system otherwise::

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
        """
        Returns the duration of the last visit to this page in the 
        current session in seconds.
        """
        *_, last_duration = self.durations()
        return last_duration

    def first_duration(self) -> float:
        """
        Returns the duration of the last visit to this page in the 
        current session in seconds.
        """
        first_duration, *_ = self.durations()
        return first_duration

    def _validate_page(self):

        if not self.has_been_shown:
            if self.must_be_shown:
                msg = self.exp.config.get("hints", "page_must_be_shown")
                self.exp.post_message(msg, level="danger")
                return False
            else:
                return True

        # check minimum display time
        mintime = self._mdt
        if time.time() - self.show_times[0] < mintime:
            msg = self.minimum_display_time_msg.format(mdt=str(mintime))
            self.exp.message_manager.post_message(msg)
            return False

        return True

    def _validate_elements(self):
        return all([el.validate_data() for el in self.input_elements.values()])


@inherit_kwargs
class Page(_CoreCompositePage):
    """
    The basic page.

    Args:
        fixed_width (str): Custom value for defining a fixed width of
            the page. Only takes effect, if the experiment is set to
            generally operate with a fixed page width in *config.conf*
            (option *responsive* in section *layout* must be "false").
            Must be a string including a unit, e.g. "900px". Can be
            defined as a class attribute.

        responsive_width (str): Custom values for definig the width of
            the page in percent of the screen width. Only takes
            effect, if the option *responsive* in section *layout* is
            "true" (which is the default). Must be a single string with
            1 to 5 relative widths separated by commas, e.g. "60%, 50%".
            The first value refers to extra small ('xs') screens, the
            following values to the next bigger ones. If the string
            contains less than five values, the last value will be used
            for all screens from that size on upward.

            The sizes are taken from Bootstrap and correspond to the
            five width attributes of a :class:`.RowLayout`.

            Can be defined as a class attribute.

        header_color (str): A color to be used for the header
            of this page. Can be any color value understood by CSS,
            including hex and RGB. Can be defined as a class
            attribute.

        background_color (str): A color to be used for the background of
            this page. Can be any color value understood by CSS,
            including hex and RGB. Can be defined as a class
            attribute.

        {kwargs}

    Notes:

        .. note:: In class style, you can use the initialization 
           arguments of a page by defining them as class attributes.
           See "How to use pages" for details.
    
    Examples:

        Basic example for adding a page with a single element in
        class style::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.Page):
                title = "This is a demo"

                def on_exp_access(self):
                    self += al.Text("This is demo text.")
            

        Example for customly defining a set of relative widths. The 
        following page will take up 80 % of available space on extra 
        small screens, 70 % on small screens, and 60 % on medium, large 
        and extra large screens::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                responsive_width = "80%, 70%, 60%"

    """

    def __init__(
        self,
        title: str = None,
        name: str = None,
        fixed_width: str = None,
        responsive_width: str = None,
        header_color: str = None,
        background_color: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(title=title, name=name, *args, **kwargs)

        self._fixed_width = None
        if fixed_width:
            self.fixed_width = fixed_width

        self._responsive_width = None
        if responsive_width:
            self.responsive_width = responsive_width

        self._header_color = None
        if header_color:
            self.header_color = header_color

        self._background_color = None
        if background_color:
            self.background_color = background_color

    @property
    def fixed_width(self) -> str:
        """
        Custom value for defining a fixed width of
        the page. Only takes effect, if the experiment is set to
        generally operate with a fixed page width in *config.conf*
        (option *responsive* in section *layout* must be "false").
        Must be a string including a unit, e.g. "900px". Can be
        defined as a class attribute.
        """
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, value):
        self._fixed_width = value

    @property
    def responsive_width(self):
        """
        Custom values for definig the width of
        the page in percent of the screen width. Only takes
        effect, if the option *responsive* in section *layout* is
        "true" (which is the default). Must be a single string with
        1 to 5 relative widths separated by commas, e.g. "60%, 50%".
        The first value refers to extra small ('xs') screens, the
        following values to the next bigger ones. If the string
        contains less than five values, the last value will be used
        for all screens from that size on upward.

        The sizes are taken from Bootstrap and correspond to the
        five width attributes of a :class:`.RowLayout`.

        Can be defined as a class attribute.
        """
        return self._responsive_width

    @responsive_width.setter
    def responsive_width(self, value):
        self._responsive_width = value

    @property
    def header_color(self):
        """
        A color to be used for the header
        of this page. Can be any color value understood by CSS,
        including hex and RGB. Can be defined as a class
        attribute.
        """
        return self._header_color

    @header_color.setter
    def header_color(self, value):
        self._header_color = value

    @property
    def background_color(self):
        """
        A color to be used for the background of
        this page. Can be any color value understood by CSS,
        including hex and RGB. Can be defined as a class
        attribute.
        """
        return self._background_color

    @background_color.setter
    def background_color(self, value):
        self._background_color = value

    def _parse_responsive_width(self, width):
        return [x.strip().replace("%", "") for x in width.split(",")]

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
        # docstring inherited
        for elmnt in self.elements.values():
            elmnt._prepare_web_widget()

    def added_to_experiment(self, experiment):
        # docstring inherited
        super().added_to_experiment(experiment)
        self._set_width()
        self._set_color()

    def _set_width(self):
        if self.experiment.config.getboolean("layout", "responsive"):

            if self.responsive_width:
                w = self._parse_responsive_width(self.responsive_width)
                self += Style(code=self._responsive_media_query(w))

            elif self.experiment.config.get("layout", "responsive_width"):
                config_width = self.experiment.config.get("layout", "responsive_width")
                w = self._parse_responsive_width(config_width)
                self += Style(code=self._responsive_media_query(w))

        elif not self.fixed_width:
            w = self.experiment.config.get("layout", "fixed_width")
            self += Style(code=f".fixed-width {{ width: {w}; }}")
            self += Style(code=f".min-width {{ min-width: {w}; }}")

        else:
            self += Style(code=f".fixed-width {{ width: {self.fixed_width}; }}")
            self += Style(code=f".min-width {{ min-width: {self.fixed_width}; }}")

    def _set_color(self):
        if self.header_color:
            self += Style(code=f".logo-bg {{background-color: {self.header_color};}}")

        elif self.experiment.config.get("layout", "header_color", fallback=False):
            c = self.experiment.config.get("layout", "header_color", fallback=False)
            self += Style(code=f".logo-bg {{background-color: {c};}}")

        if self.background_color:
            self += Style(code=f"body {{background-color: {self.background_color};}}")

        elif self.experiment.config.get("layout", "background_color", fallback=False):
            c = self.experiment.config.get("layout", "background_color", fallback=False)
            self += Style(code=f"body {{background-color: {c};}}")

    @property
    def _css_code(self):
        return reduce(lambda l, element: l + element.css_code, self.elements.values(), [])

    @property
    def _css_urls(self):
        return reduce(lambda l, element: l + element.css_urls, self.elements.values(), [])

    @property
    def _js_code(self):
        return reduce(lambda l, element: l + element.js_code, self.elements.values(), [])

    @property
    def _js_urls(self):
        return reduce(lambda l, element: l + element.js_urls, self.elements.values(), [])

@inherit_kwargs
class WidePage(Page):
    """
    A page with a wider default width.

    Args:
        {kwargs}

    Notes:
        The width of this page is only customized for responsive layouts.
        If you disabled responsive layout, it will have default width.
    
    Examples:
        A minimal experiment with a single wide page, holding a text
        element::
            
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.WidePage):
                title = "This is a demo"

                def on_exp_access(self):
                    self += al.Text("This is demo text.")
    
    """

    responsive_width = "85%, 75%, 75%, 70%"

@inherit_kwargs
class NoNavigationPage(Page):
    """
    A page without navigation buttons.
    
    Args:
        {kwargs}
    
    Examples:
        A minimal experiment with a single NoNavigationPage, from which
        participants can move forward via the SubmittingButtons::
            
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.NoNavigationPage):
                title = "This is a demo"

                def on_exp_access(self):
                    
                    self += al.SubmittingButtons(
                        "Yes", "No", 
                        toplab="Do you agree to this statement?",
                        name="submit1"
                        )
    """

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self += Style("#page-navigation {display: none;}")


@inherit_kwargs
class TimeoutPage(Page):
    """
    A page with an additional hook that gets triggered after a timeout.
    
    The timeout starts when the page is shown for the first time. If a
    page is shown for a second time, the timeout will not run again.

    Args:
        timeout (str): Length of the timeout. Specify it as a string 
            with a unit of "s" for seconds, and "m" for minutes, 
            for example "10s". Can be specified as a class attribute.
        {kwargs}
    
    See Also:
        Timeout hook: :meth:`~.Page.on_timeout`
    
    Examples:
        A minimal experiment with a single TimeoutPage, holding a text
        element. The navigating buttons are hidden through the 
        :class:`.HideNavigation` element.
        
        The *on_timeout* hook shows the implementation of the
        :class:`.AutoForwardPage`. The page will move forward after the
        timeout of 5 seconds expires::
            
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.TimeoutPage):
                title = "This is a demo"
                timeout = "5s"

                def on_exp_access(self):
                    self += al.Text("This is demo text.")
                    self += al.HideNavigation()
                
                def on_timeout(self):
                    self.exp.forward()
    """

    timeout = None

    def __init__(self, timeout: str = None, **kwargs):
        super().__init__(**kwargs)

        self._end_link = "unset"
        self._run_timeout = True
        if timeout is not None:
            self.timeout = timeout

        if self.timeout is None:
            raise AlfredError("A TimeoutPage must have a 'timeout' attribute.")

        unit = self.timeout[-1]
        if unit == "s":
            self.timeout = int(self.timeout[:-1])
        elif unit == "m":
            self.timeout = int(self.timeout[:-1]) * 60
        else:
            raise ValueError(
                "You must specify the unit of your timeout ('s' - seconds, or 'm' - minutes)"
            )

    def added_to_experiment(self, experiment):
        # docstring inherited
        super().added_to_experiment(experiment)
        self._end_link = self._experiment.user_interface_controller.add_callable(self._callback)

        if self._experiment.config.getboolean("general", "debug"):
            if self._experiment.config.getboolean("debug", "reduce_countdown"):
                self.timeout = self._experiment.config.getint("debug", "reduced_countdown_time")

    @property
    def _js_code(self):
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
            % (self.timeout, self._end_link),
        )
        js_code = super()._js_code
        if self._run_timeout:
            js_code.append(code)
        else:
            js_code.append((5, """$(document).ready(function(){$(".timeout-label").html(0);});"""))
        return js_code

    def _callback(self, **kwargs):
        self._run_timeout = False
        self._experiment.movement_manager.current_page._set_data(kwargs)
        self.on_timeout()

    def on_timeout(self):
        """
        Executed *once*, after the timeout of the page runs out.

        See Also:
            See "How to use hooks" for a how to on using hooks and an overview
            of available hooks.

            This hook is defined by :class:`.AutoForwardPage` and
            :class:`.AutoClosePage`.
        """
        pass


@inherit_kwargs
class AutoForwardPage(TimeoutPage):
    """
    A page that automatically moves forward after the timeout expires.

    Args:
        {kwargs}

    Notes:
        This page will work with customly defined :meth:`.custom_move`
        methods.

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.AutoForwardPage):
                timeout = "5s"

                def on_exp_access(self):
                    self += al.Text("This page will move after 5 seconds.")

    """

    def on_timeout(self):
        self.experiment.movement_manager.move(direction="forward")


@inherit_kwargs
class AutoClosePage(TimeoutPage):
    """
    A page that automatically closes itself after the timeout expires.

    Args:
        {kwargs}

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class DemoPage(al.AutoClosePage):
                timeout = "5s"

                def on_exp_access(self):
                    self += al.Text("This page will close after 5 seconds.")

    """

    def on_timeout(self):
        self.close()


@inherit_kwargs
class NoDataPage(Page):
    """
    A page that does not save any data.

    Args:
        {kwargs}
    
    Notes:
        This page *will* still trigger a saving event upon moving,
        so that, for example, updates to the :attr:`.ExperimentSession.adata` 
        dictionary will be saved. It just does not save any data itself,
        i.e. input elements on this page will not appear in the data.
    
    See Also:
        See :class:`.NoSavingPage` for a page that does not trigger a
        saving event.
    """

    data = {}

@inherit_kwargs
class NoSavingPage(Page):
    """
    A page that does not trigger a saving event on moving.

    Args:
        {kwargs}
    
    Notes:
        This page will not trigger any saving action on its own. But if
        experiment data is saved at another point of the experiment, data
        collected on a NoSavingPage *will* be saved. You can switch off 
        this behavior by overriding the *data* attribute, effectively
        creating a NoDataNoSavingPage (see Example 2).

        Note also that upon finishing, the experiment will always trigger
        a saving event, even if you only have NoSavingPages in your
        experiment. To prevent this, you can switch the option 
        'save_data' in section 'data' of config.conf to 'false'.

    See Also:
        See :class:`.NoDataPage` for a page that does not collect any
        data.
    
    Examples:

        Example 1, simple usage::

            import alfred3 as al
            exp = al.Experiment()
            exp += al.NoSavingPage(name="demo")

        Example 2, a NoSavingPage that also does not collect any data::

            import alfred3 as al
            exp = al.Experiment()

            class NoDataNoSavingPage(al.NoSavingPage):

                data = {{}}
            
            exp += NoDataNoSavingPage(name="demo")
        
        Example 3, a more elaborate example. Here, we create an 
        experiment with an "admin" mode, triggered by an url parameter,
        in which no data will be saved.
        Note that, if we use this method, we do not even need to use
        a NoSavingPage::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp):
                admin = exp.urlargs.get("admin", False)
                if admin == "true":
                    exp.config.read_dict({{"data": {{"save_data": "false"}}}})
                    exp.log.info("Admin mode triggered. No data will be saved")

            exp += al.Page(name="demo")
        
        If this experiment is started with the suffix ``?admin=true`` to
        the starting url, no data will be saved. In case of a locally 
        running experiment, the url would be 
        http://localhost:5000/start?admin=true

        .. note:: Note that the experiment will most likely crash, if
            the /start route gets called twice for any reason in a local
            experiment.

    """

    def save_data(self, *args, **kwargs):
        """
        This page type does not save data on its own, so this method has
        no effect.
        """
        pass


@inherit_kwargs
class UnlinkedDataPage(NoDataPage):
    """
    A page that saves data separately from the experiment data.

    Args:
        encrypt (str): Takes one the following values: 'agent' (default) will
            encrypt data based on each saving agent's configuration.
            'always' will encrypt all data entered on this page,
            regardless of saving agent configuration. 'never' will turn
            off encryption for this page, regardless of saving agent
            configuration. Can be specified as a class attribute.
        {kwargs}

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

    .. warning::
        All data from UnlinkedDataPages is saved in a single unlinked
        data document, so data from two different unlinked pages *are*
        linked to each other (though not to the rest of the experiment
        data).

    """

    encrypt: str = "agent"

    def __init__(self, encrypt: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if encrypt is not None:
            self.encrypt = encrypt

        if self.encrypt not in ["agent", "always", "never"]:
            raise ValueError(
                "The argument 'encrypt' must take one of the following values: 'agent', 'always', 'never'."
            )

    @property
    def unlinked_data(self) -> dict:
        # docstring inherited
        if not self.has_been_shown:
            return {}
        else:
            data = {}
            for element in self.input_elements.values():
                data.update(element.data)
            return data

    def save_data(self, level: int = 1, sync: bool = False):
        """
        Saves current unlinked data.

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


class _CustomSavingPage(Page, ABC):
    """
    TODO: This class still needs some work.

    Allows you to add custom SavingAgents directly to the page.

    Args:
        save_to_main: If True, data will be *also* saved using the
            experiment's main SavingAgentController and all of its
            SavingAgents. Defaults to False. Can be specified as a
            class attribute.

    Notes:
        Since this is an abstract class, it can not be instantiated directly.
        You have to derive a child class and define the property
        :meth:`custom_save_data`, which must return a dictionary. Through
        this property, you control exactly which data will be saved by this
        page.

        .. warning::
            Each SavingAgent maintains one file or one document.
            On saving, the document will be fully replaced with the current
            data. That means, you should not let two CustomSavingPages
            share a SavingAgent, as they will override each other's data.
            That is, unless that is your intended behavior, e.g. when the
            pages share data.

    Examples:
        Example 1: Saving ordinary page data (like other pages)::

            class MyPage(CustomSavingPage):

                @property
                def custom_save_data(self):
                    return self.data


        Example 2: Saving a static dictionary::

            class MyPage(CustomSavingPage):

                @property
                def custom_save_data(self):
                    return {"key": "value"}
    """

    save_to_main: bool = False

    def __init__(self, save_to_main: bool = None, **kwargs):
        super().__init__(**kwargs)
        
        if save_to_main is not None:
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
        """
        Appends saving agents to this page.

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


class _DefaultFinalPage(Page):
    """
    The default final page.
    """

    title = "Experiment beendet"

    def on_exp_access(self):
        txt = "Das Experiment ist nun beendet.<br>Vielen Dank für die Teilnahme."
        self += elm.display.Text(":mortar_board:", font_size=70, align="center")
        self += elm.display.VerticalSpace("20px")
        self += elm.display.Text(text=txt, align="center")
        self += elm.misc.WebExitEnabler()
