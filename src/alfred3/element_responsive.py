# -*- coding:utf-8 -*-
"""Provides element classes for adding content to pages.

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>
"""
import random
import re
import string
import logging

from abc import ABC, abstractproperty, abstractmethod
from pathlib import Path
from typing import List
from typing import Union
from dataclasses import dataclass

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import Template
from past.utils import old_div

import cmarkgfm
from emoji import emojize

from . import alfredlog
from ._helper import alignment_converter
from ._helper import fontsize_converter
from ._helper import is_url

jinja_env = Environment(loader=PackageLoader(__name__, "templates/elements"))


def icon(name: str, ml: int = 0, mr: int = 0) -> str:
    """Returns HTML code for displaying font-awesome icons.
    
    These icons can be used in all places where HTML code is rendered,
    i.e. TextElements, and all labels of elements.


    Example::
        
        TextElement(f"Camera Icon: {icon('camera')}")

    If you need more control, you can simply use the HTML code directly
    and apply classes and styles as you wish::
        
        TextElement("<i class='fas fa-camera'></i>")
    
    Args:
        name: The icon name, as shown on https://fontawesome.com/icons?d=gallery&m=free
        ml: Margin to the left, can be an integer from 0 to 5.
        mr: Margin to the right, can be an integer from 0 to 5.

    """
    return f"<i class='fas fa-{name} ml-{ml} mr-{mr}'></i>"


def emoji(text: str) -> str:
    """Returns a unicode representation of emojis, based on shortcodes.
    
    The emoji printing can be used in all TextElements and Element labels.
    Overview of Shortcodes: https://www.webfx.com/tools/emoji-cheat-sheet/

    Example::
        
        TextElement(f"Joy emoji: {emoji(':joy:')}")

    You can also print unicode emojis directly without the help of this
    function, using the "CLDR Short Name" as defined on the official
    unicode website [#unicode]_ ::

        TextElement("Joy emoji: \\N{face with tears of joy}")

    Args:
        text: Text, containing emoji shortcodes.
    
    .. [#unicode] http://www.unicode.org/emoji/charts/full-emoji-list.html

    """
    return emojize(text, use_aliases=True)


class RowLayout:
    """ 
    Args:
        responsive: Boolean, indicating whether breakpoints should
                    be responsive, or not.
    """

    def __init__(self, ncols: int, valign_cols: List[str] = None, responsive: bool = True):
        self.ncols = ncols
        self._valign_cols = valign_cols
        self.responsive = responsive

        self.width_xs = None
        self.width_sm = None
        self.width_md = None
        self.width_lg = None
        self.width_xl = None

    def col_breaks(self, col: int) -> str:
        """Returns the column breakpoints for a specific column as 
        strings for use as bootstrap classes.
        
        Args:
            col: Column index (starts at 0)
        """
        xs = self.format_breaks(self.width_xs, "xs")[col]
        sm = self.format_breaks(self.width_sm, "sm")[col]
        md = self.format_breaks(self.width_md, "md")[col]
        lg = self.format_breaks(self.width_lg, "lg")[col]
        xl = self.format_breaks(self.width_xl, "xl")[col]

        if self.responsive:
            breaks = [xs, sm, md, lg, xl]
            if breaks == ["", "", "", "", ""]:
                return "col-sm"
            else:
                return " ".join(breaks)
        else:  # set breaks to a fixed value
            breaks = self.format_breaks(self.width_sm, "xs")[col]  # this is ONE value
            out = breaks if breaks != "" else "col"
            return out

    def format_breaks(self, breaks: List[int], bp: str) -> List[str]:
        """Takes a tuple of column sizes (in integers from 1 to 12) and
        returns a corresponding list of formatted Bootstrap column 
        classes.

        Args:
            breaks: List of integers, indicating the breakpoints.
            bp: Specifies the relevant bootstrap breakpoint. (xs, sm,
                md, lg, or xl).
        """
        try:
            if len(breaks) > self.ncols:
                raise ValueError(
                    "Break list must be of the same or smaller length as number of elements."
                )
        except TypeError:
            pass

        out = []
        for i in range(self.ncols):
            try:
                n = breaks[i]
            except (IndexError, TypeError):
                out.append("")
                continue

            if not isinstance(n, int):
                raise TypeError("Break values must be of type integer.")
            if not n >= 1 and n <= 12:
                raise ValueError("Break values must be between 1 and 12.")

            if bp == "xs":
                out.append(f"col-{n}")
            else:
                out.append(f"col-{bp}-{n}")

        return out

    @property
    def valign_cols(self) -> List[str]:
        try:
            if len(self._valign_cols) > self.ncols:
                raise ValueError(
                    "Col position list must be of the same or smaller length as number of elements."
                )
        except TypeError:
            pass

        out = []
        for i in range(self.ncols):
            try:
                n = self._valign_cols[i]
            except (IndexError, TypeError):
                out.append("align-self-center")
                continue

            if not isinstance(n, str):
                raise TypeError("Col position must be of type str.")

            if n == "auto":
                out.append("")
            elif n == "top":
                out.append("align-self-start")
            elif n == "center":
                out.append("align-self-center")
            elif n == "bottom":
                out.append("align-self-end")
            else:
                raise ValueError(
                    "Col position allowed values are 'auto', 'top', 'center', and 'bottom'."
                )

        return out

    @valign_cols.setter
    def valign_cols(self, value: List[str]):
        self._valign_cols = value


class Element(ABC):
    """Element baseclass. 
    
    Elements are derived from this class. Most of them inherit its 
    arguments, attributes, and methods, unless stated otherwise.

    The simplest way to subclass *Element* is by defining the 
    *inner_html* attribute::

        class NewElement(Element):

            inner_html = "Element html goes <b>here</b>"
    
    For most cases, you will want some additional control over the 
    attribute. Maybe you even want to use your own jinja template. 
    You can achieve that by defining *inner_html* as a property, which 
    returns your desired html code::

        import jinja2

        class NewElement(Element):

            @property
            def inner_html(self):
                t = jinja2.Template("Element html goes <b>{{ text }}</b>")
                return t.render(text="here")
    
    Both of the above methods utilise alfred's basic element html 
    template and inject your code into it, which allows the basic layout
    and logic to simply translate to your new element. If your new
    Element has its own *__init__* constructor method, you can pass
    specific arguments or all available arguments on to the Element 
    base class::

        # define new argument 'myarg' and save it as an attribute
        # set a new default for argument width and pass it on to the 
        # Element base class allow all other valid keyword arguments for 
        # the Element base class and pass them on ('**kwargs')
        
        class NewElement(Element):

            def __init__(self, myarg: str = "test", width: str = "narrow", **kwargs):
                super().__init__(width=width, **kwargs)
                self.myarg = myarg
        

    .. note::
        All elements that are derived in this way receive a CSS class
        of their class name, which can be used for css styling (i.e. a
        new element 'ExampleElement' receives the CSS class 
        'ExampleElement'). Further, all elements receive a html element
        ID of the form 'elid-<name>', where <name> is replaced by the
        element's name attribute. This can be used to style individual
        elements via CSS.
    
    If you want full control over the element's html template, you can
    redefine the *web_widget* property. This will overwrite the
    basic html layouting functionality. Example::

        class NewElement(Element):

            @property
            def web_widget(self):
                return "This property should return your full desired code."

    Args:
        name: Name of the element. This should be a unique identifier.
            It will be used to identify the corresponding data in the
            final data set. If none is provided, a generic name will be
            generated.
        font_size: Font size for text in the element. Can be 'normal' 
            (default), 'big', 'huge', or an integer giving the desired 
            size in pt.
        align: Alignment of text/instructions inside the element. 
            Can be 'left' (default), 'center', 'right', or 'justify'.
        position: Horizontal position of the full element on the 
            page. Values can be 'left', 'center' (default), 'end',
            or any valid value for the justify-content flexbox
            utility [#bs_flex]_ .
        width: Defines the horizontal width of the element from 
            small screens upwards. It's always full-width on extra
            small screens. Possible values are 'narrow', 'medium',
            'wide', and 'full'. For more detailed control, you can 
            define the *element_width* attribute.
        height: Vertical height. Supply a string with a unit, e.g.
            "80px".
        showif: A dictionary, defining conditions that must be met
            for the element to be shown. See :attr:`showif` for details.
        should_be_shown_filter_function: (...)
        instance_level_logging: If *True*, the element will use an
            instance-specific logger, thereby allowing detailed fine-
            tuning of its logging behavior.
        alignment: Alignment of text/instructions inside the element. 
            Can be 'left' (default), 'center', 'right', or 'justify'. 
            *Deprecated in v1.5*. Please use *align*. 

    Attributes:
        element_width: A list of relative width definitions. The
            list can contain up to 5 width definitions, given as
            integers from 1 to 12. They refer to the five breakbpoints 
            in Bootstrap 4's 12-column-grid system, i.e. 
            [xs, sm, md, lg, xl] [#bs_grid]_ .
        experiment: The alfred experiment to which this element belogs.
        log: An instance of :class:`alfred3.logging.QueuedLoggingInterface`,
            which is a modified interface to python's logging facility
            [#log]_ . You can use it to log messages with the standard
            logging methods 'debug', 'info', 'warning', 'error', 
            'exception', and 'log'. It also offers direct access to the
            logger via ``log.queue_logger``.
        page: The element's parent page (i.e. the page on which it is
            displayed).
        showif: The showif dictionary. It must be of the form
            ``{<page_uid>: {<element_name>: <value>}}``. It can contain
            showifs for multiple pages and for multiple elements on 
            each page. The element will only be shown if *all* 
            conditions are met.
    
    .. [#bs_flex] see https://getbootstrap.com/docs/4.0/utilities/flex/#justify-content
    .. [#bs_grid] see https://getbootstrap.com/docs/4.0/layout/grid/
    .. [#log] see https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    """

    base_template = jinja_env.get_template("Element.html")
    element_template = None
    can_display_corrective_hints_in_line = False

    def __init__(
        self,
        name: str = None,
        font_size: Union[str, int] = None,
        align: str = "left",
        width: str = "full",
        height: str = None,
        position: str = "center",
        showif: dict = None,
        instance_level_logging: bool = False,
        **kwargs,
    ):

        # general
        self.name = name
        self.page = None
        self.experiment = None

        # display settings
        self.align = align
        self.font_size = font_size
        self.width = width
        self.height = height
        self.position = position
        self._show_corrective_hints = False
        self._element_width = None
        self._maximum_widget_width = None

        # showifs and filters
        self._enabled = True
        self.showif = showif if showif else {}
        self._showif_on_current_page = False
        self._should_be_shown = True

        # additional code
        self._css_code = []
        self._css_urls = []
        self._js_code = []
        self._js_urls = []

        # logging
        self.instance_level_logging = instance_level_logging
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)

        # Catch unsupported keyword arguments
        if kwargs != {}:
            raise ValueError(f"Parameter '{list(kwargs.keys())[0]}' is not supported.")

    # getters and setter start here ------------------------------------

    @property
    def converted_width(self):
        if self.width == "narrow":
            return ["col-12", "col-sm-6", "col-md-3"]
        elif self.width == "medium":
            return ["col-12", "col-sm-9", "col-md-6"]
        elif self.width == "wide":
            return ["col-12", "col-md-9"]
        elif self.width == "full":
            return ["col-12"]

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if value not in ["narrow", "medium", "wide", "full"] and value is not None:
            raise ValueError(f"'{value}' is not a valid width.'")
        self._width = value

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if value == "left":
            self._position = "start"
        elif value == "right":
            self._position = "end"
        else:
            self._position = value

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = fontsize_converter(value)

    @property
    def element_width(self):
        if self.width is not None:
            return " ".join(self.converted_width)

        width = self._element_width if self._element_width is not None else ["col-12"]
        if self.experiment.config.getboolean("layout", "responsive", fallback=True):
            return " ".join(width)
        else:
            return width[0]

    @element_width.setter
    def element_width(self, value: List[int]):
        self._element_width = value

    @property
    def name(self):
        """
        Property **name** marks a general identifier for element, which is also used as variable name in experimental datasets.
        Stored input data can be retrieved from dictionary returned by :meth:`.data_manager.DataManager.get_data`.
        """
        return self._name

    @name.setter
    def name(self, name):
        if name is None:
            self._name = None

        elif name is not None:
            if not re.match(r"^[-_A-Za-z0-9]*$", name):
                raise ValueError(
                    "Element names may only contain following charakters: A-Z a-z 0-9 _ -"
                )

            if not isinstance(name, str):
                raise TypeError

            self._name = name

    @property
    def data(self):
        """
        Property **data** contains a dictionary with input data of element.
        """
        return {}

    @property
    def corrective_hints(self):
        return []

    @property
    def show_corrective_hints(self):
        return self._show_corrective_hints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        self._show_corrective_hints = bool(b)

    @property
    def should_be_shown(self):
        """
        Returns True if should_be_shown is set to True (default) and all should_be_shown_filter_functions return True.
        Otherwise False is returned
        """
        cond1 = self._should_be_shown
        cond2 = all(self._evaluate_showif())
        return cond1 and cond2

    @should_be_shown.setter
    def should_be_shown(self, b):
        """
        sets should_be_shown to b.

        :type b: bool
        """
        if not isinstance(b, bool):
            raise TypeError("should_be_shown must be an instance of bool")
        self._should_be_shown = b

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = value

    @property
    def tree(self):
        return self.page.tree

    @property
    def identifier(self):
        return self.tree.replace("rootSection_", "") + "_" + self._name

    @property
    def css_code(self):
        return self._css_code

    @property
    def css_urls(self):
        return self._css_urls

    @property
    def js_code(self):
        return self._js_code

    @property
    def js_urls(self):
        return self._js_urls

    @property
    def web_thumbnail(self):
        return None

    @property
    def template_data(self):
        d = {}
        d["element_class"] = self.element_class
        d["name"] = self.name
        d["position"] = self.position
        d["element_width"] = self.element_width
        d["hide"] = "hide" if self._showif_on_current_page is True else ""
        d["align"] = f"text-{self.align}"
        d["align_raw"] = self.align
        d["fontsize"] = f"font-size: {self.font_size}pt;" if self.font_size is not None else ""
        d["height"] = f"height: {self.height};" if self.height is not None else ""
        d["responsive"] = self.experiment.config.getboolean("layout", "responsive")
        return d

    # Private methods start here ---------------------------------------

    def _evaluate_showif(self) -> List[bool]:
        """Checks the showif conditions that refer to previous pages.
        
        Returns:
            A list of booleans, indicating for each condition whether
            it is met or not.
        """

        if self.showif:
            conditions = []
            for page_uid, condition in self.showif.items():

                # skip current page (showifs for current pages are checked elsewhere)
                if page_uid == self.page.uid:
                    continue

                d = self.experiment.get_page_data(page_uid=page_uid)
                for target, value in condition.items():
                    try:
                        conditions.append(d[target] == value)
                    except KeyError:
                        msg = (
                            f"You defined a showif '{target} == {value}' for {self} "
                            f"on Page with uid '{page_uid}', "
                            f"but {target} was not found on the page. "
                            "The element will NOT be shown."
                        )
                        self.log.warning(msg)
                        self.should_be_shown = False
                        return
            return conditions
        else:
            return [True]

    def _activate_showif_on_current_page(self):
        """Adds JavaScript to self for dynamic showif functionality."""
        on_current_page = self.showif.get(self.page.uid, None)
        if on_current_page:

            # If target element is not even on the same page
            for element_name, value in on_current_page.items():
                if not element_name in self.page.element_dict:
                    msg = (
                        f"You defined a showif '{element_name} == {value}' for {self} "
                        f"on {self.page}, "
                        f"but {element_name} was not found on the page. "
                        "The element will NOT be shown."
                    )
                    self.log.warning(msg)
                    self.should_be_shown = False
                    return

            t = jinja_env.get_template("showif.js")
            js = t.render(showif=on_current_page, element=self.name)
            self.js_code.append((7, js))
            self._showif_on_current_page = True

    # Public methods start here ----------------------------------------

    def added_to_experiment(self, experiment):
        """Tells the element that it was added to an experiment. 
        
        The experiment is made available to the element, and the 
        element's logging interface initializes its experiment-specific
        logging.

        Args:
            experiment: The alfred experiment to which the element was
                added.
        """
        self.experiment = experiment

        queue_logger_name = self.prepare_logger_name()
        self.log.queue_logger = logging.getLogger(queue_logger_name)
        self.log.session_id = self.experiment.config.get("metadata", "session_id")
        self.log.log_queued_messages()

    def added_to_page(self, page):
        """Tells the element that it was added to a page. 
        
        The page and the experiment are made available to the element.

        Args:
            page: The page to which the element was added.
        """
        from . import page as pg

        if not isinstance(page, pg.PageCore):
            raise TypeError()

        self._page = page
        if self.name is None:
            self.name = self.page.generate_element_name(self)

        if self.page.experiment:
            self.added_to_experiment(self._page.experiment)

    def set_data(self, data):
        pass

    def validate_data(self):
        return True

    def prepare(self):
        """Wraps *prepare_web_widget* to allow for additional, generic
        preparations that are the same for all elements.
        
        This is useful, because *prepare_web_widget* is often redefined
        in derived elements.
        """
        self._activate_showif_on_current_page()
        self.prepare_web_widget()

    def prepare_web_widget(self):
        """Hook for computations for preparing an element's web widget.
        
        This method is supposed to be overridden by derived elements if
        necessary.
        """
        pass

    def prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name.class_uid
        
        with *class_uid* only added, if 
        :attr:`~Element.instance_level_logging` is set to *True*.
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self.experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        if self.instance_level_logging and self._name:
            name.append(self._name)

        return ".".join(name)

    # Magic methods start here -----------------------------------------

    def __str__(self):
        return f"{type(self).__name__}(name: '{self.name}')"

    def __repr__(self):
        return self.__str__()

    # abstract attributes start here -----------------------------------

    @property
    def inner_html(self):
        if self.element_template is not None:
            return self.element_template.render(self.template_data)
        else:
            return None

    @property
    def web_widget(self):
        """Every child class *must* redefine the web widget.
        
        This is the html-code that defines the element's display on the
        screen.
        """
        d = self.template_data
        d["html"] = self.inner_html
        return self.base_template.render(d)

    @property
    def element_class(self):
        return type(self).__name__


@dataclass
class Column:
    breaks: str
    vertical_position: str
    element: Element
    id: str


class Row(Element):
    """Allows you to arrange up to 12 elements in a row.

    The row will arrange your elements using Bootstrap 4's grid system
    and breakpoints, making the arrangement responsive. You can 
    customize the behavior of the row for five different screen sizes
    (Bootstrap 4's default break points) with the width attributes.

    If you don't specify breakpoints manually, the columns will default
    to equal width and wrap on breakpoints automatically.

    .. info::
        In Bootstrap's grid, the horizontal space is divided into 12
        equally wide units. You can define the horizontal width of a
        column by assigning it a number of those units. A column of 
        width 12 will take up all available horizontal space, other 
        columns will be placed below such a full-width column.

        You can define the column width for each of five breakpoints
        separately. The definition will be valid for screens of the
        respective size up to the next breakpoint.

        See https://getbootstrap.com/docs/4.5/layout/grid/#grid-options 
        for detailed documentation of how Bootstrap's breakpoints work.
    
    .. info::
        **Some information regarding the width attributes**
        
        - If you specify fewer values than the number of columns in the 
        width attributes, the columns with undefined width will take up 
        equal portions of the remaining horizontal space.
        - If a breakpoint is not specified manually, the values from the
        next smaller breakpoint are inherited.
    
    Args:
        elements: The elements that you want to arrange in a row.
        height: Custom row height (with unit, e.g. '100px').
        valign_cols: List of vertical column alignments. Valid values 
            are 'auto' (default), 'top', 'center', and 'bottom'.
        elements_full_width: A switch, telling the row whether you wish
            it to resize all elements in it to full-width (default: True).
    
    Attributes:
        width_xs: List of column widths on screens of size 'xs' or 
            bigger (<576px). Widths must be defined as integers between
            1 and 12.
        width_sm: List of column widths on screens of size 'sm' or 
            bigger (>=576px). Widths must be defined as integers between
            1 and 12.
        width_md: List of column widths on screens of size 'md' or 
            bigger (>=768px). Widths must be defined as integers between
            1 and 12.
        width_lg: List of column widths on screens of size 'lg' or 
            bigger (>=992px). Widths must be defined as integers between
            1 and 12.
        width_xl: List of column widths on screens of size 'xl' or 
            bigger (>=1200px). Widths must be defined as integers between
            1 and 12.
    """

    def __init__(
        self,
        *elements,
        height: str = "auto",
        valign_cols: List[str] = None,
        name: str = None,
        showif: dict = None,
        elements_full_width: bool = True,
    ):
        """Constructor method."""
        super().__init__(name=name, showif=showif)
        self.elements = elements
        self.layout = RowLayout(ncols=len(self.elements), valign_cols=valign_cols)
        self.height = height
        self.elements_full_width = elements_full_width

    def added_to_page(self, page):
        super().added_to_page(page)

        for element in self.elements:
            if element is None:
                continue
            element.should_be_shown = False
            page += element

            if self.elements_full_width:
                element.width = "full"

    @property
    def css_code(self):
        if not self.height == "auto":
            css = f"#elid-{self.name} {{height: {self.height};}}"
            return [(10, css)]
        else:
            return []

    @property
    def cols(self) -> list:
        """Returns a list of columns."""
        out = []
        for i, element in enumerate(self.elements):
            col = Column(
                breaks=self.layout.col_breaks(col=i),
                vertical_position=self.layout.valign_cols[i],
                element=element,
                id=f"{self.name}_col{i+1}",
            )
            out.append(col)
        return out

    @property
    def web_widget(self):
        d = {}
        d["hide"] = "hide" if self._showif_on_current_page is True else ""
        d["columns"] = self.cols
        d["name"] = self.name
        t = jinja_env.get_template("Row.html")
        return t.render(d)


class Stack(Row):
    def __init__(self, *elements, **kwargs):
        super().__init__(*elements, **kwargs)
        self.layout.width_xs = [12 for element in elements]


class VerticalSpace(Element):
    """The easiest way to add vertical space to a page.
    
    Args:
        space: Desired space in any unit that is understood by a CSS
            margin (e.g. em, px, cm). Include the unit (e.g. '1em').
    """

    def __init__(self, space: str = "1em"):
        """Constructor method."""
        super().__init__()
        self.space = space

    @property
    def web_widget(self):
        return f"<div style='margin-bottom: {self.space};'></div>"


class Style(Element):
    """Adds CSS code to a page. 
    
    CSS styling can be used to change the appearance of page or 
    individual elements. 
    
    .. note:: 
        A Style is added to a specific page, and thus only affects the 
        layout of that page. To change the appearance of the whole 
        experiment, you can define your styles in a .css file and 
    """

    web_widget = None
    should_be_shown = False

    def __init__(self, code: str = None, url: str = None, path: str = None, priority: int = 10):
        super().__init__()
        self.priority = priority
        self.code = code
        self.url = url

        self.path = Path(path) if path is not None else None
        self.should_be_shown = False

        if (self.code and self.path) or (self.code and self.url) or (self.path and self.url):
            raise ValueError("You can only specify one of 'code', 'url', or 'path'.")

    @property
    def css_code(self):
        if self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def css_urls(self):
        return [(self.priority, self.url)]


class HideNavigation(Style):

    def __init__(self):
        super().__init__()
        self.code = "#page-navigation {display: none;}"


class JavaScript(Element):
    """Adds JavaScript to a page.
    
    Javascript can be used to implement dynamic behavior on the client
    side.
    """

    web_widget = None
    should_be_shown = False

    def __init__(self, code: str = None, url: str = None, path: str = None, priority: int = 10):
        super().__init__()
        self.priority = priority
        self.code = code
        self.url = url

        self.path = Path(path) if path is not None else None
        self.should_be_shown = False

        if (self.code and self.path) or (self.code and self.url) or (self.path and self.url):
            raise ValueError("You can only specify one of 'code', 'url', or 'path'.")

    @property
    def js_code(self):
        if self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def js_urls(self):
        return [(self.priority, self.url)]


class WebExitEnabler(JavaScript):
    """If added to a page, this element disables the 'Do you really want
    to leave this page?' popup on that page."""

    def __init__(self):
        code = "$(document).ready(function(){glob_unbind_leaving();});"
        super().__init__(code=code, priority=10)


class TextElement(Element):
    """Displays text.

    You can use GitHub-flavored Markdown syntax [#md]_ and common emoji 
    shortcodes [#emoji]_ . Additionally, you can use raw html for 
    advanced formatting.

    Example::

        TextElement("**This is boldfaced** text. :blush:")

    Text can be entered directly through the `text` parameter, or
    it can be read from a file by specifying the 'path' parameter.
    Note that you can only use one of these options, if you specify
    both, the element will raise an error.

    .. example::
        # Text element with responsive width
        text = TextElement('Text display')

        # Text element that is always displayed as full-width
        text = TextElement('Text display', width='full')

        # Text element with content read from file
        text = TextElement(path='files/text.md')
        
    Args:
        text: Text to be displayed.
        text_width: Text width in px. **Deprecated** for responsive
            design (v1.5). Use `element_width` instead, when using
            the responsive design.
        text_height: Element height in px.
        path: Filepath to a textfile (relative to the experiment 
            directory).
        width: Element width. Usage is the same as in 
            :class:`Element`, but the TextElement uses its own
            specific default, which ensures good readability in 
            most cases on different screen sizes.
        **element_args: Keyword arguments passed to the parent class
            :class:`Element`. Accepted keyword arguments are: name, 
            font_size, align, width, position, showif, 
            instance_level_logging.
    
    Attributes:
        emojize: If True (default), emoji shortcodes in the text will
            be converted to unicode.

    .. [#md]: https://guides.github.com/features/mastering-markdown/
    .. [#emoji]: Overview of Shortcodes: https://www.webfx.com/tools/emoji-cheat-sheet/
    """

    element_class = "text-element"
    element_template = jinja_env.get_template("TextElement.html")
    emojize = True

    def __init__(
        self, text: str = None, path: Union[Path, str] = None, width: str = None, **element_args,
    ):

        """Constructor method."""
        super().__init__(width=width, **element_args)

        self._text = text if text is not None else ""
        self.path = path

        if self._text and self.path:
            raise ValueError("You can only specify one of 'text' and 'path'.")

    @property
    def text(self):
        if self.path:
            return self.experiment.subpath(self.path).read_text()
        else:
            return self._text

    def render_text(self):
        if self.emojize:
            text = emojize(self.text, use_aliases=True)
        else:
            text = self.text
        return cmarkgfm.github_flavored_markdown_to_html(text)

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def element_width(self):
        if self.width is not None:
            return " ".join(self.converted_width)

        responsive = self.experiment.config.getboolean("layout", "responsive", fallback=True)
        if responsive:
            if self._element_width is None:
                return " ".join(["col-12", "col-sm-11", "col-lg-10", "col-xl-9"])
            else:
                return " ".join(self._element_width)
        elif not responsive:
            return "col-9"

    @property
    def template_data(self) -> dict:
        d = super().template_data
        d["text"] = self.render_text()
        # height = f"height: {self._text_height}px;" if self._text_height is not None else ""
        # d["style"] += f"{height}"

        return d

    def __str__(self):
        if len(self.text) <= 10:
            text = self.text
        else:
            text = self.text[0:10] + "..."

        return f"{type(self).__name__}(text: '{text}'; name: '{self.name}')"


class Hline(Element):
    element_class = "hline-element"
    inner_html = "<hr>"

class CodeElement(TextElement):
    """A convenience element for displaying highlighted code.

    Args:
        lang: The programming language to highlight [#lang]_ . Defaults 
            to 'auto', which tries to auto-detect the right language. 
    
    .. [#lang] see https://prismjs.com/index.html#supported-languages
        for an overview of possible language codes. Note though that 
        we may not support all possible languages.
    """

    element_class = "code-element"

    def __init__(
        self,
        text: str = None,
        path: Union[Path, str] = None,
        lang: str = "auto",
        width: str = "full",
        **element_args,
    ):

        """Constructor method."""
        super().__init__(text=text, path=path, width=width, **element_args)
        self.lang = lang if lang is not None else ""

    @property
    def text(self):
        if self.path:
            text = self.experiment.subpath(self.path).read_text()

            code = f"```{self.lang}\n{text}\n```"
            return code
        else:
            code = f"```{self.lang}\n{self._text}\n```"
            return code

    def __str__(self):
        text = self.text.replace(f"```{self.lang}", "").replace("\n", "").replace("\r", "")
        if len(self.text) > 10:
            text = text[0:10] + " ..."

        return f"{type(self).__name__}(text: '{text}'; lang: '{self.lang}'; name: '{self.name}')"


class Label(TextElement):
    """A child of TextElement, serving mainly as label for other 
    elements.
    """

    element_class = "label-element"

    def __init__(self, text, width="full", **kwargs):
        super().__init__(text=text, width=width, **kwargs)
        self.layout: RowLayout = None
        self.layout_col: int = None

    @property
    def col_breaks(self):
        return self.layout.col_breaks(self.layout_col)

    @property
    def vertical_alignment(self):
        return self.layout.valign_cols[self.layout_col]


class DataElement(Element):
    """DataElement can be used to save data without any display.

    Example::

        DataElement(value="test", name="mydata")
    
    Args:
        value: The value that you want to save.
    """

    def __init__(self, value: Union[str, int, float], description: str = None, **kwargs):
        """Constructor method."""

        if kwargs.pop("variable", False):
            raise ValueError("'variable' is not a valid parameter. Use 'value' instead.")

        super(DataElement, self).__init__(**kwargs)
        self.value = value
        self.description = description
        self.should_be_shown = False

    @property
    def data(self):
        return {self.name: self.value}

    @property
    def encrypted_data(self):
        encrypted_value = self.experiment.encrypt(self.value)
        return {self.name: encrypted_value}

    @property
    def codebook_data_flat(self):
        from . import page

        data = {}
        data["name"] = self.name
        data["tree"] = self.tree.replace("rootSection_", "")
        data["identifier"] = self.identifier
        data["page_title"] = self.page.title
        data["element_type"] = type(self).__name__
        data["description"] = self.description
        data["duplicate_identifier"] = False
        data["unlinked"] = True if isinstance(self.page, page.UnlinkedDataPage) else False
        return data

    @property
    def codebook_data(self):
        return {self.identifier: self.codebook_data_flat}

    def __str__(self):
        return f"{type(self).__name__}(value: '{self.value}'; name: '{self.name}')"


class LabelledElement(Element):
    """An intermediate Element class which provides support for labels.
    
    Args:
        toplab, leftlab, rightlab, bottomlab: Strings or instances of
            :class:`Label`, which will be used to label the element.
        layout: A list of integers, specifying the allocation of 
            horizontal space between leftlab, main element widget and
            rightlab. Uses Bootstraps 12-column-grid, i.e. you can
            choose integers between 1 and 12.
    """

    base_template = jinja_env.get_template("LabelledElement.html")
    element_class = "labelled-element"

    def __init__(
        self,
        toplab: str = None,
        leftlab: str = None,
        rightlab: str = None,
        bottomlab: str = None,
        layout: List[int] = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(**kwargs)
        # default for width
        if leftlab and rightlab:
            # for accessing the right col in layout.col_breaks for the input field
            self.input_col = 1
            self.layout = RowLayout(ncols=3)
            self.layout.width_sm = layout if layout is not None else [2, 8, 2]
        elif leftlab:
            # for accessing the right col in layout.col_breaks for the input field
            self.input_col = 1
            self.layout = RowLayout(ncols=2)
            self.layout.width_sm = layout if layout is not None else [3, 9]
        elif rightlab:
            # for accessing the right col in layout.col_breaks for the input field
            self.input_col = 0
            self.layout = RowLayout(ncols=2)
            self.layout.width_sm = layout if layout is not None else [9, 3]
        else:
            # for accessing the right col in layout.col_breaks for the input field
            self.input_col = 0
            self.layout = RowLayout(ncols=1)
            self.layout.width_sm = [12]

        self.layout.valign_cols = ["center" for el in range(self.layout.ncols)]

        self.toplab = toplab
        self.leftlab = leftlab
        self.rightlab = rightlab
        self.bottomlab = bottomlab

    def added_to_page(self, page):
        super().added_to_page(page)

        for lab in ["toplab", "leftlab", "rightlab", "bottomlab"]:
            if getattr(self, lab):
                getattr(self, lab).name = f"{self.name}-{lab}"

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self.layout.responsive = self.experiment.config.getboolean("layout", "responsive")

        if self.toplab:
            self.toplab.added_to_experiment(experiment)

        if self.leftlab:
            self.leftlab.added_to_experiment(experiment)

        if self.rightlab:
            self.rightlab.added_to_experiment(experiment)

        if self.bottomlab:
            self.bottomlab.added_to_experiment(experiment)

    @property
    def toplab(self):
        """Label above of the main element widget."""
        return self._toplab

    @toplab.setter
    def toplab(self, value: str):
        if isinstance(value, Label):
            self._toplab = value
        elif isinstance(value, str):
            self._toplab = Label(text=value, align="center")
        else:
            self._toplab = None

    @property
    def bottomlab(self):
        """Label below of the main element widget."""
        return self._bottomlab

    @bottomlab.setter
    def bottomlab(self, value: str):
        if isinstance(value, Label):
            self._bottomlab = value
        elif isinstance(value, str):
            self._bottomlab = Label(text=value, align="center")
        else:
            self._bottomlab = None

    @property
    def leftlab(self):
        """Label to the left of the main element widget."""
        return self._leftlab

    @leftlab.setter
    def leftlab(self, value: str):
        if isinstance(value, Label):
            self._leftlab = value
            self._leftlab.layout = self.layout
            self._leftlab.layout_col = 0
        elif isinstance(value, str):
            self._leftlab = Label(text=value, align="right")
            self._leftlab.layout = self.layout
            self._leftlab.layout_col = 0
        else:
            self._leftlab = None

    @property
    def rightlab(self):
        """Label to the right of the main element widget."""
        return self._rightlab

    @rightlab.setter
    def rightlab(self, value: str):
        if isinstance(value, Label):
            self._rightlab = value
            self._rightlab.layout = self.layout
            self._rightlab.layout_col = self.input_col + 1
        elif isinstance(value, str):
            self._rightlab = Label(text=value, align="left")
            self._rightlab.layout = self.layout
            self._rightlab.layout_col = self.input_col + 1
        else:
            self._rightlab = None

    @property
    def labels(self) -> str:
        """Returns the labels in a single, nicely formatted string."""

        labels = []
        if self.toplab:
            labels.append(f"top: '{self.toplab.text}'")
        if self.leftlab:
            labels.append(f"left: '{self.leftlab.text}'")
        if self.rightlab:
            labels.append(f"right: '{self.rightlab.text}'")
        if self.bottomlab:
            labels.append(f"bottom: '{self.bottomlab.text}'")

        if labels:
            return ", ".join(labels)

    def __str__(self):
        return f"{type(self).__name__}(labels: {self.labels}; name: {self.name})"

    @property
    def template_data(self):
        d = super().template_data
        d["toplab"] = self.toplab
        d["leftlab"] = self.leftlab
        d["rightlab"] = self.rightlab
        d["bottomlab"] = self.bottomlab
        d["input_breaks"] = self.layout.col_breaks(col=self.input_col)
        d["input_valign"] = self.layout.valign_cols[self.input_col]
        return d


class InputElement(LabelledElement):
    """Base class for elements that allow data input.

    This class handles the logic und layouting of instructions for input 
    elements.

    Args:
        no_input_corrective_hint: Hint to be displayed if force_input 
            set to True and no user input registered. Defaults to the
            experiment-wide value specified in config.conf.
        instruction_width: Horizontal width of instructions. 
            **Deprecated** for responsive design (v1.5+). Use 
            `instruction_col_width` instead, when using the responsive 
            design.
        instruction_height: Minimum vertical size of instruction label.
        force_input: If `True`, users can only progress to the next page
            if they enter data into this field. **Note** that this works
            only in HeadOpenSections and SegmentedSections, not in plain
            Sections.
        description: An additional description of the element. This will
            show up in the additional alfred-generated codebook. It has
            no effect on the display of the experiment.
        default: Default value.
        **kwargs: Further keyword arguments that are passed on to the
            parent class :class:`Element`.
    
    Attributes:
        instruction_col_width: Width of the instruction area, using
            Bootstrap's 12-column-grid. You can assign an integer 
            between 1 and 12 here to fine-tune the instruction width.
        input_col_width: Width of the input area, using
            Bootstrap's 12-column-grid. You can assign an integer 
            between 1 and 12 here to fine-tune the input area width.
    """

    can_display_corrective_hints_in_line = True
    disabled = False

    def __init__(
        self,
        toplab: str = None,
        force_input: bool = False,
        no_input_corrective_hint: str = None,
        default=None,
        description: str = None,
        disabled: bool = False,
        **kwargs,
    ):
        super().__init__(toplab=toplab, **kwargs)
        self.description = description

        self._input = ""
        self._force_input = force_input
        self._no_input_corrective_hint = no_input_corrective_hint
        self._default = default

        if disabled:
            self.disabled = disabled

        if default is not None:
            self._input = default

        if self._force_input and (self._showif_on_current_page or self.showif):
            raise ValueError(f"Elements with 'showif's can't be 'force_input' ({self}).")

    @property
    def debug_value(self):
        name = f"{type(self).__name__}_default"
        return self.experiment.config.get("debug", name, fallback=None)

    @property
    def debug_enabled(self) -> bool:
        if self.experiment.config.getboolean("general", "debug"):
            if self.experiment.config.getboolean("debug", "set_default_values"):
                return True
        return False

    @property
    def default(self):
        if self._default:
            return self._default
        elif self.debug_enabled:
            return self.debug_value
        else:
            return None
    
    @default.setter
    def default(self, value):
        self._default = value

    @property
    def force_input(self):
        return self._force_input
    
    @force_input.setter
    def force_input(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("Force input must be a boolean value.")

        self._force_input = value

    @property
    def template_data(self) -> dict:
        d = super().template_data
        d["default"] = self.default
        d["input"] = self.input
        d["disabled"] = self.disabled

        if self.corrective_hints:
            d["corrective_hint"] = self.corrective_hints[0]

        return d

    def validate_data(self):
        return not self._force_input or not self._should_be_shown or bool(self._input)

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._force_input and not self._input:
            return [self.no_input_hint]
        else:
            return super(InputElement, self).corrective_hints

    @property
    def no_input_hint(self):
        if self._no_input_corrective_hint:
            return self._no_input_corrective_hint
        return self.default_no_input_hint

    @property
    def default_no_input_hint(self):
        name = f"no_input{type(self).__name__}"
        return self.experiment.config.get("hints", name, fallback="You need to enter something.")

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    @property
    def data(self):
        return {self.name: self.input}

    @property
    def encrypted_data(self):
        """Returns the element's data with encrypted values."""
        enrcypted_dict = {}
        for k, v in self.data.items():
            try:
                enrcypted_dict[k] = self.experiment.encrypt(v)
            except TypeError:
                if isinstance(v, list):
                    v = [self.experiment.encrypt(entry) for entry in v]
                enrcypted_dict[k] = v

        return enrcypted_dict

    def set_data(self, d):
        if not self.disabled:
            self._input = d.get(self.name, "")

    @property
    def codebook_data_flat(self):
        from . import page

        data = {}
        data["name"] = self.name
        data["label_top"] = self.toplab.text if self.toplab is not None else ""
        data["label_left"] = self.leftlab.text if self.leftlab is not None else ""
        data["label_right"] = self.rightlab.text if self.rightlab is not None else ""
        data["label_bottom"] = self.bottomlab.text if self.bottomlab is not None else ""
        data["tree"] = self.tree.replace("rootSection_", "")
        data["identifier"] = self.identifier
        data["page_title"] = self.page.title
        data["element_type"] = type(self).__name__
        data["force_input"] = self._force_input
        data["default"] = self.default
        data["description"] = self.description
        data["duplicate_identifier"] = False
        data["unlinked"] = True if isinstance(self.page, page.UnlinkedDataPage) else False
        return data

    @property
    def codebook_data(self):
        return {self.identifier: self.codebook_data_flat}


class TextEntryElement(InputElement):
    """Provides a text entry field.

    Args:
        prefix: Prefix for the input field.
        suffix: Suffix for the input field.
        placeholder: Placeholder text, displayed inside the input field.
        default: Default value.
        **kwargs: Further keyword arguments that are passed on to the
            parent class :class:`InputElement`.
        
    """

    element_class = "text-entry-element"
    element_template = jinja_env.get_template("TextEntryElement.html")

    def __init__(
        self,
        toplab: str = None,
        prefix: str = None,
        suffix: str = None,
        placeholder: str = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(toplab=toplab, **kwargs)

        self._prefix = prefix
        self._suffix = suffix
        self._placeholder = placeholder if placeholder is not None else ""

    @property
    def prefix(self):
        return self._prefix

    @property
    def suffix(self):
        return self._suffix

    @property
    def placeholder(self):
        return self._placeholder

    @property
    def template_data(self):
        d = super().template_data
        d["placeholder"] = self.placeholder
        d["prefix"] = self.prefix
        d["suffix"] = self.suffix
        return d

    def validate_data(self):
        super(TextEntryElement, self).validate_data()

        if self._force_input and self._should_be_shown and self._input == "":
            return False

        return True

    @property
    def codebook_data_flat(self):
        data = super().codebook_data_flat
        data["prefix"] = self.prefix
        data["suffix"] = self.suffix
        data["placeholder"] = self.placeholder

        return data


class TextAreaElement(TextEntryElement):
    element_class = "text-area-element"
    element_template = jinja_env.get_template("TextAreaElement.html")

    def __init__(self, toplab: str = None, nrows: int = 5, **kwargs):
        super().__init__(toplab=toplab, **kwargs)
        self.area_nrows = nrows

    @property
    def template_data(self):
        d = super().template_data
        d["area_nrows"] = self.area_nrows
        return d


@dataclass
class Choice:
    """Dataclass for managing choices."""

    label: str = None
    label_id: str = None
    id: str = None
    name: str = None
    value: str = None
    type: str = "radio"
    checked: bool = False
    css_class: str = None


class ChoiceElement(InputElement, ABC):
    element_class = "choice-element"
    element_template = jinja_env.get_template("ChoiceElement.html")
    type = None
    emojize: bool = True

    def __init__(
        self,
        *choice_labels,
        vertical: bool = False,
        shuffle: bool = False,
        align: str = "center",
        **kwargs,
    ):
        super().__init__(align=align, **kwargs)

        self.choice_labels = choice_labels
        self.vertical = vertical
        self.shuffle = shuffle

        if self.shuffle:
            random.shuffle(self.choice_labels)

    def added_to_page(self, page):
        super().added_to_page(page)

        for label in self.choice_labels:
            if isinstance(label, Element):
                label.added_to_page(page)
                label.should_be_shown = False
                label.width = "full"  # in case of TextElement, b/c its default is a special width

    def prepare_web_widget(self):
        self.choices = self.define_choices()

    @property
    def template_data(self):
        d = super().template_data
        d["choices"] = self.choices
        d["vertical"] = self.vertical
        return d

    @abstractmethod
    def define_choices(self) -> list:
        pass


class SingleChoiceElement(ChoiceElement):
    """ 
    """

    element_class = "single-choice-element"
    type = "radio"

    def define_choices(self):
        choices = []
        for i, label in enumerate(self.choice_labels, start=1):
            choice = Choice()

            if isinstance(label, Element):
                choice.label = label.web_widget
            else:
                if self.emojize:
                    label = emojize(str(label), use_aliases=True)
                choice.label = cmarkgfm.github_flavored_markdown_to_html(str(label))
            choice.type = "radio"
            choice.value = i
            choice.name = self.name
            choice.id = f"choice{i}-{self.name}"
            choice.label_id = f"{choice.id}-lab"

            if self.debug_enabled:
                choice.checked = True if i == 1 else False
            elif self.input:
                choice.checked = True if int(self.input) == i else False
                # import pdb; pdb.set_trace()
            elif self.default:
                choice.checked = True if (self.default == i) else False

            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)
        return choices

    @property
    def codebook_data_flat(self):
        # import pdb; pdb.set_trace()
        d = super().codebook_data_flat

        choices = {f"choice{i+1}": str(lab) for i, lab in enumerate(self.choice_labels)}
        d.update(choices)
        return d


class SingleChoiceButtons(SingleChoiceElement):
    """

    "align" parameter has no effect in labels.

    Keyword Arguments:
        button_width: Can be used to manually define the width of 
            buttons. If you supply a single string, the same width will
            be applied to all buttons in the element. If you supply
            "auto", button width will be determined automatically. You 
            can also supply a list of specific widths for each 
            individual button. You must specify a unit, e.g. '140px'. 
            Defaults to "equal".
        button_style: Can be used for quick color-styling, using 
            Bootstraps default color keywords: btn-primary, btn-secondary,
            btn-success, btn-info, btn-warning, btn-danger, btn-light, 
            btn-dark. You can also use the "outline" variant to get 
            outlined buttons (eg. "btn-outline-secondary"). If you 
            specify a single string, this style is applied to all 
            buttons in the element. If you supply a list, you can define
            individual styles for each button. If you supply a list that
            is shorter than the list of labels, the last style
            will be repeated for remaining buttons. Advanced user can
            supply their own CSS classes for button-styling.
        button_toolbar: A boolean switch to toggle whether buttons should
            be layoutet as a connected toolbar (*True*), or as separate
            neighbouring buttons (*False*, default).
        button_round_corners: A boolean switch to toggle whether buttons
            should be displayed with additionally rounded corners 
            (*True*). Defaults to *False*.
    """

    element_class: str = "single-choice-buttons"
    element_template = jinja_env.get_template("ChoiceButtons.html")

    button_toolbar: bool = False
    button_group_class: str = "choice-button-group"
    button_round_corners = True

    def __init__(
        self,
        *choice_labels,
        button_width: Union[str, list] = "equal",
        button_style: Union[str, list] = "btn-outline-dark",
        button_corners: str = None,
        **kwargs,
    ):
        super().__init__(*choice_labels, **kwargs)
        self.button_width = button_width
        self.button_style = button_style
        if button_corners is not None and button_corners == "normal":
            self.button_round_corners = False

    @property
    def button_style(self):
        return self._button_style

    @button_style.setter
    def button_style(self, value):

        # create list of fitting length, if only string is provided
        if isinstance(value, str):
            self._button_style = [value for x in self.choice_labels]

        # take styles-list if the length fits
        elif isinstance(value, list) and len(value) == len(self.choice_labels):
            self._button_style = value

        # repeat last value, if styles-list is shorter than labels-list
        elif isinstance(value, list) and len(value) < len(self.choice_labels):
            self._button_style = []
            for i, _ in enumerate(self.choice_labels):
                try:
                    self._button_style.append(value[i])
                except IndexError:
                    self._button_style.append(value[-1])

        elif isinstance(value, list) and len(value) > len(self.choice_labels):
            raise ValueError("List of button styles cannot be longer than list of button labels.")

    @property
    def template_data(self):
        d = super().template_data
        d["button_style"] = self.button_style
        d["button_group_class"] = self.button_group_class
        d["align_raw"] = self._convert_alignment()
        return d

    def _button_width(self):
        """Add css for button width."""

        if self.button_width == "equal":
            if not self.vertical:
                # set button width to small value, because they will grow to fit the group
                css = f".btn.choice-button-{self.name} {{width: 10px;}} " 
            else:
                css = []
            # full-width buttons on small screens
            css += (
                f"@media (max-width: 576px) {{.btn.choice-button-{self.name} {{width: 100%;}}}} "
            )
            self._css_code += [(7, css)]

        elif isinstance(self.button_width, str):
            # the group needs to be switched to growing with its member buttons
            css = f"#choice-button-group-{self.name} {{width: auto;}} "
            # and return to 100% with on small screens
            css += f"@media (max-width: 576px) {{#choice-button-group-{self.name} {{width: 100%!important;}}}} "
            
            # now the width of the individual button has an effect
            css += f".btn.choice-button-{self.name} {{width: {self.button_width};}} "
            # and it, too returns to full width on small screens
            css += (
                f"@media (max-width: 576px) {{.btn.choice-button-{self.name} {{width: 100%;}}}} "
            )
            self._css_code += [(7, css)]

        elif isinstance(self.button_width, list):
            if not len(self.button_width) == len(self.choices):
                raise ValueError(
                    "Length of list 'button_width' must equal length of list 'choices'."
                )

            # the group needs to be switched to growing with its member buttons
            css = f"#choice-button-group-{self.name} {{width: auto;}} "
            # and return to 100% with on small screens
            css += f"@media (max-width: 576px) {{#choice-button-group-{self.name} {{width: 100%!important;}}}}"
            self._css_code += [(7, css)]

            # set width for each individual button
            for w, c in zip(self.button_width, self.choices):
                css = f"#{c.label_id} {{width: {w};}} "
                css += f"@media (max-width: 576px) {{#{c.label_id} {{width: 100%!important;}}}} "
                self._css_code += [(7, css)]

    def _round_corners(self):
        """Adds css for rounded buttons."""

        spec = "border-radius: 1rem;"
        css = f"div#choice-button-group-{ self.name }.btn-group>label.btn.choice-button {{{spec}}}"
        self._css_code += [(7, css)]

    def _toolbar(self):
        """Adds css for toolbar display instead of separate buttons."""

        not_ = "last", "first"
        margin = "right", "left"

        for exceptn, m in zip(not_, margin):
            n = "0" if m == "right" else "-1px"
            spec = f"margin-{m}: {n}; "
            spec += f"border-top-{m}-radius: 0; "
            spec += f"border-bottom-{m}-radius: 0;"
            css = f"div#choice-button-group-{ self.name }.btn-group>.btn.choice-button:not(:{exceptn}-child) {{{spec}}}"
            self._css_code += [(7, css)]

    def _convert_alignment(self):
        if self.vertical:
            if self.align == "center":
                return "align-self-center"
            elif self.align == "left":
                return "align-self-start"
            elif self.align == "right":
                return "align-self-end"
        else:
            return None

    def prepare_web_widget(self):
        super().prepare_web_widget()

        if self.button_toolbar:
            self._toolbar()

        if self.button_round_corners:
            self._round_corners()

        if not self.button_width == "auto":
            self._button_width()


class SingleChoiceBar(SingleChoiceButtons):
    element_class = "single-choice-bar"
    button_group_class = "choice-button-bar"  # this leads to display as connected buttons
    button_toolbar = True
    button_round_corners = True


class MultipleChoiceElement(ChoiceElement):
    """ 

    Defining 'min', 'max' implies force_input.
    """

    element_class = "multiple-choice-element"
    type = "checkbox"

    def __init__(
        self, *choice_labels, min: int = None, max: int = None, select_hint: str = None, default: list = None, **kwargs,
    ):
        super().__init__(*choice_labels, **kwargs)

        self._input = {}

        if min is not None or max is not None:
            self.force_input = True

        self.min = min if min is not None else 0
        self.max = max if max is not None else len(self.choice_labels)
        self._select_hint = select_hint

        if default is not None and not isinstance(default, list):
            raise ValueError("Default for MultipleChoiceElement must be a list of integers, indicating the default choices.")
        else:
            self.default = default

    @property
    def select_hint(self):
        if self._select_hint:
            return self._select_hint
        else:
            hint = string.Template(
                self.experiment.config.get("hints", "select_MultipleChoiceElement")
            )
            return hint.substitute(min=self.min, max=self.max)

    @property
    def corrective_hints(self):

        if not self.show_corrective_hints:
            return []

        elif self._force_input and not self._input:
            return [self.no_input_hint]

        elif not self.validate_data():
            return [self.select_hint]

    def validate_data(self):
        if not self.force_input or not self._should_be_shown:
            return True
        elif self.min <= sum(list(self.input.values())) <= self.max:
            return True
        else:
            return False

    @property
    def data(self):
        return self._input

    def set_data(self, d):
        self._input = {}
        for choice in self.choices:
            value = d.get(choice.name, None)
            if value:
                self._input[choice.name] = True
            else:
                self._input[choice.name] = False

    def define_choices(self):
        choices = []
        for i, label in enumerate(self.choice_labels, start=1):
            choice = Choice()

            if isinstance(label, Element):
                choice.label = label.web_widget
            else:
                if self.emojize:
                    label = emojize(str(label), use_aliases=True)
                choice.label = cmarkgfm.github_flavored_markdown_to_html(str(label))
            choice.type = "checkbox"
            choice.value = label
            choice.id = f"choice{i}-{self.name}"
            choice.name = choice.id
            choice.label_id = f"{choice.id}-lab"
            choice.css_class = f"choice-button choice-button-{self.name}"

            if self.debug_enabled:
                choice.checked = True if i <= self.max else False
            elif self.input:
                choice.checked = True if self.input[choice.name] is True else False
            elif self.default:
                choice.checked = True if i in self.default else False

            choices.append(choice)
        return choices


class MultipleChoiceButtons(MultipleChoiceElement, SingleChoiceButtons):
    element_class = "multiple-choice-buttons"
    button_round_corners = False


class MultipleChoiceBar(MultipleChoiceButtons):
    element_class = "multiple-choice-bar"
    button_group_class = "choice-button-bar"
    button_toolbar = True
    button_round_corners = False


class ButtonLabels(SingleChoiceButtons):

    element_class = "button-choice-labels"
    disabled = True

    @property
    def data(self):
        return {}


class BarLabels(SingleChoiceBar):

    element_class = "bar-choice-labels"
    disabled = True

    @property
    def data(self):
        return {}


class SubmittingButtons(SingleChoiceButtons):
    element_class = "submitting-buttons"

    def added_to_page(self, page):
        super().added_to_page(page)

        t = jinja_env.get_template("submittingbuttons.js")
        js = t.render(name=self.name)

        page += JavaScript(code=js)


class ImageElement(Element):
    element_class = "image-element"
    element_template = jinja_env.get_template("ImageElement.html")

    def __init__(self, path: Union[str, Path] = None, url: str = None, **kwargs):
        super().__init__(**kwargs)

        self.path = path
        if url is not None and not is_url(url):
            raise ValueError("Supplied value is not a valid url.")
        else:
            self.url = url

        if path and url:
            raise ValueError("You can only specify one of 'path' and 'url'.")

        self.src = None

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        if self.path:
            p = self.experiment.subpath(self.path)
            url = self.experiment.user_interface_controller.add_static_file(p)
            self.src = url
        else:
            self.src = self.url

    @property
    def template_data(self):
        d = super().template_data
        d["src"] = self.src
        return d

    def __str__(self):
        src = self.path if self.path is not None else self.url
        return f"ImageElement(src: '{src}'; name: '{self.name}')"

