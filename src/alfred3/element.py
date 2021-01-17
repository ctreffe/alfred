# -*- coding:utf-8 -*-
"""
Provides element classes for adding content to pages.

All elements are derived from the base :class:`.Element`. There are 
currently four kinds of elements:

- **Display elements** are used to present something
- **Input elements** are used to allow subject input
- **Action elements** trigger some kind of action, when they are 
  interacted with.
- **Utility elements** are used for different kinds of handy things

  The following tables give an overview over all of these elements.


.. csv-table:: Element bases
    :header: "Element Name", "Description"
    :widths: 20, 80

    :class:`.Element`           , Basis for all elements
    :class:`.LabelledElement`   , Basis for elements with labels
    :class:`.InputElement`      , Basis for elements with user input
    :class:`.RowLayout`         , Basis for horizontal layouting


.. csv-table:: Display Elements
   :header: "Element Name", "Description"
   :widths: 20, 80

   :class:`.Html`           ,   Displays html code
   :class:`.Text`           ,   "Displays text. Can render Markdown, html, and emoji shortcodes"
   :class:`.Alert`          ,   Displays text in alert boxes
   :class:`.CodeBlock`      ,   Displays code with syntax highlighting
   :class:`.Image`          ,   Displays an image
   :class:`.Audio`          ,   Plays sound
   :class:`.Video`          ,   Displays a video
   :class:`.MatPlot`        ,   Displays a :class:`matplotlib.figure.Figure` 
   :class:`.Hline`          ,   Displays a horizontal line on the page
   :class:`.ButtonLabels`   ,   Additional labels for :class:`.SingleChoiceButtons` or :class:`.MultipleChoiceButtons`
   :class:`.BarLabels`      , Additional labels for :class:`.SingleChoiceBar` or :class:`MultipleChoiceBar`

.. csv-table:: Input Elements
   :header: "Element Name", "Description"
   :widths: 20, 80

   :class:`.TextEntry`              ,   A simple text entry field
   :class:`.TextArea`               ,   A text area field for multiline input
   :class:`.RegEntry`               ,   TextEntry with input validation via regular expressions
   :class:`.NumberEntry`            ,   TextEntry that specializes on numbers
   :class:`.SingleChoice`           ,   "Radiobuttons, allowing selection of one out of several options"
   :class:`.SingleChoiceList`       ,   "Dropdown list, allowing selection of one out of several options"
   :class:`.SingleChoiceButtons`    ,   "Buttons, allowing selection of one out of several options"
   :class:`.SingleChoiceBar`        ,   Toolbar of SingleChoiceButtons
   :class:`.MultipleChoice` ,   "Checkboxes, allowing selection of multiple options"
   :class:`.MultipleChoiceButtons`  ,   "Buttons, allowing selection of multiple options"
   :class:`.MultipleChoiceBar`      ,   Toolbar of MultipleChoiceButtons
   :class:`.MultipleChoiceList`     ,   "Scrollable list, allowing selection of multiple options"


.. csv-table:: Action Elements
   :header: "Element Name", "Description"
   :widths: 20, 80

   :class:`.SubmittingButtons`  ,   Buttons which trigger the experiment to move forward on click
   :class:`.JumpButtons`        ,   Buttons which trigger the experiment to jump to a specific page on click
   :class:`.DynamicJumpButtons` ,   "JumpButtons, which get their target page dynamically from another element on the same page"
   :class:`JumpList`            ,   Dropbown of pages for jumping



.. csv-table:: Utility Elements
   :header: "Element Name", "Description"
   :widths: 20, 80

   :class:`.Row`            ,   Aligns multiple elements horizontally in a row
   :class:`.Stack`          ,   Stacks multiple elements in a row on top of each other. Think "multi-row-cell"
   :class:`.VerticalSpace`  ,   Adds vertical space
   :class:`.Style`          ,   Adds CSS code to a page
   :class:`.JavaScript`     ,   Adds JavaScript code to a page
   :class:`.HideNavigation` ,   Removes to navigation buttons from a page
   :class:`.WebExitEnabler` ,   Turns the "Do you really want to leave?" dialogue upon closing of a page off
   :class:`.Value`          ,   Saves a value to the experiment data without displaying anything
   :class:`.Data`           ,   Alias for :class:`.Value`


.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>, Paul Wiemann <paulwiemann@gmail.com>
"""

import random
import re
import string
import logging
import io

from abc import ABC, abstractproperty, abstractmethod
from pathlib import Path
from typing import List
from typing import Tuple
from typing import Union
from typing import Iterator
from dataclasses import dataclass
from uuid import uuid4

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import Template
from past.utils import old_div

import cmarkgfm
from emoji import emojize

from . import alfredlog
from .messages import MessageManager
from .exceptions import AlfredError
from ._helper import alignment_converter
from ._helper import fontsize_converter
from ._helper import is_url
from ._helper import check_name

#: jinja2.Environment, giving access to included jinja-templates.
#: :meta private:
jinja_env = Environment(loader=PackageLoader(__name__, "templates/elements"))
"""jinja2.Environment, giving access to included jinja-templates."""


class RowLayout:
    """
    Provides layouting functionality for responsive horizontal
    positioning of elements.

    Default behavior is to have equal-width columns with an automatic
    breakpoint on extra small screens (i.e. all columns get the bootstrap
    class 'col-sm' by default).

    The layout's width attributes can be accessed an changed to customize
    appearance. In this example, we change the width of the columns on
    screens of "small" and bigger width, so that we have narrow columns
    to the right and left (each taking up 2/12 of the available space),
    and one wide column (taking up 8/12 of the space) in the middle. On
    "extra small" screens, the columns will be stacked vertically and
    each take up the full width.

    You can define widths for five breakpoints individually, allowing
    for fine-grained control (see attributes).

    Args:
        ncols: Number of columns to arrange in a row.
        valign_cols: List of vertical column alignments. Valid values
            are 'auto' (default), 'top', 'center', and 'bottom'.
        responsive: Boolean, indicating whether breakpoints should
            be responsive, or not.

    Examples:

        ::

            layout = RowLayout(ncols=3) # 3 columns of equal width
            layout.width_sm = [2, 8, 2]

    """

    def __init__(self, ncols: int, valign_cols: List[str] = None, responsive: bool = True):
        """Constructor method."""
        #: Number of columns
        self.ncols: int = ncols

        self._valign_cols = valign_cols if valign_cols is not None else []

        #: Indicates whether breakpoints should be responsive, or not.
        self.responsive: bool = responsive

        #: List of column widths on screens of size 'xs' or bigger
        #: (<576px). Content must be integers between 1 and 12.
        self.width_xs: List[int] = None

        #: List of column widths on screens of size 's' or bigger
        #: (>=576px). Content must be integers between 1 and 12.
        self.width_sm: List[int] = None

        #: List of column widths on screens of size 'md' or bigger
        #: (>=768px). Content must be integers between 1 and 12.
        self.width_md: List[int] = None

        #: List of column widths on screens of size 'lg' or bigger
        #: (>=992px). Content must be integers between 1 and 12.
        self.width_lg: List[int] = None

        #: List of column widths on screens of size 'xl' or bigger
        #: (>=1200px). Content must be integers between 1 and 12.
        self.width_xl: List[int] = None

    def col_breaks(self, col: int) -> str:
        """
        Returns the column breakpoints for a specific column as
        strings for use as bootstrap classes.

        Args:
            col: Column index (starts at 0)

        Returns:
            str: Column breakpoints for a specific column
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
        """
        Takes a list of column sizes (in integers from 1 to 12) and
        returns a corresponding list of formatted Bootstrap column
        classes.

        Args:
            breaks: List of integers, indicating the breakpoints.
            bp: Specifies the relevant bootstrap breakpoint. (xs, sm,
                md, lg, or xl).

        Returns:
            List[str]: List of ready-to-use bootstrap column classes
        """
        try:
            if len(breaks) > self.ncols:
                raise ValueError("Break list length must be <= number of elements.")
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
        """
        List[str]: Vertical column alignments.

        Valid values are 'auto' (default), 'top', 'center', and 'bottom'.
        Can be specified upon initalization or modified as instance
        attribute.

        Each element of the list refers to one column. If it contains
        fewer elements than the number of columns, the last entry of
        the list will be used as value for the unreferenced columns.

        Examples:

            All columns of the following layout will be aligned to the
            bottom of the row (specified upon initialization)::

                layout1 = RowLayout(ncols=3, valign_cols=["bottom"])

            The first column of the following layout will be aligned top,
            the 2nd and 3rd columns will be aligned bottom (specified after
            initialization)::

                layout2 = RowLayout(ncols=3)
                layout2.valign_cols = ["top", "bottom"]

        """

        out = []
        for i in range(self.ncols):
            try:
                n = self._valign_cols[i]
            except IndexError:
                try:
                    n = self._valign_cols[i - 1]
                except IndexError:
                    n = "center"

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
                raise ValueError("Valign allowed values: 'auto', 'top', 'center', and 'bottom'.")

        return out

    @valign_cols.setter
    def valign_cols(self, value: List[str]):
        if len(value) > self.ncols:
            raise ValueError("Col position list length must be <= number of elements.")
        self._valign_cols = value


class Element:
    """
    Element baseclass, providing basic functionality for all elements.

    Args:
        name: Name of the element. This should be a unique identifier.
            It will be used to identify the corresponding data in the
            final data set.
        font_size: Font size for text in the element. Can be 'normal'
            (default), 'big', 'huge', or an integer giving the desired
            size in pt.
        align: Horizontal alignment of text in the element. Does not
            usually apply to labels. Think of it as an alignment that
            applies to the innermost layer of an element (while labels
            are generally located at outer layers). See
            :class:`.LabelledElement` for more on labelled elements.
            Can be 'left' (default), 'center', 'right', or 'justify'.
        position: Horizontal position of the full element on the
            page. Values can be 'left', 'center' (default), 'end',
            or any valid value for the justify-content `flexbox
            utility`_. Takes effect only, when the element is not
            full-width.
        width: Defines the horizontal width of the element from
            small screens upwards. It's always full-width on extra
            small screens. Possible values are 'narrow', 'medium',
            'wide', and 'full'. For more detailed control, you can
            define the :attr:`.element_width` attribute.
        height: Vertical height of the element's display area. Supply a
            string with a unit, e.g. "80px". Usually, the default is
            fine. For adding vertical space to a page, you should prefer
            the :class:`.VerticalSpace` element, as it is sematically
            more clear.
        showif: A dictionary, defining conditions that must be met
            for the element to be shown. The conditions take the form of
            key-value pairs, where each key is an element name and the
            value is the required input. See :attr:`showif` for details.
        instance_level_logging: If *True*, the element will use an
            instance-specific logger, thereby allowing detailed fine-
            tuning of its logging behavior.

    See Also:
        * How to create a custom element

    Notes:
        The Element does not have its own display. It is used only
        to inherit functionality.

    .. _flexbox utility: https://getbootstrap.com/docs/4.0/utilities/flex/#justify-content
    .. _Bootstrap 4's 12-column-grid system: https://getbootstrap.com/docs/4.0/layout/grid/
    .. _logging facility: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

    """

    #: Base template for the element, which will be used to hold the
    #: rendered element template. Gets rendered by :attr:`.web_widget`
    base_template: Template = jinja_env.get_template("Element.html.j2")

    #: The element's specific, inner template. Gets rendered by
    #: :attr:`.inner_html`
    element_template: Template = None

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
    ):

        self.name: str = name  # documented in getter property

        #: The element's parent :class:`~.page.Page` (i.e. the page on which
        #: it is displayed).
        self.page = None

        #: The :class:`.Experiment` to which this element belongs
        self.exp = None

        #: Alias for :attr:`.exp`
        self.experiment = None

        #: Alignment of inner element (does not apply to labels)
        self.align = align

        #: Vertical height of the element
        self.height = height

        self.font_size = font_size  # documented in getter property
        self.width = width  # documented in getter property
        self.position = position  # documented in getter property
        self._element_width = None  # documented in getter property

        # showifs and filters
        self.showif = showif if showif else {}  # documented in getter property

        #: Flag, indicating whether the element has a showif condition
        #: that includes an element on the same page
        self._showif_on_current_page = False
        self._should_be_shown = True  # documented in getter property

        # additional code
        self._css_code = []  # documented in getter property
        self._css_urls = []  # documented in getter property
        self._js_code = []  # documented in getter property
        self._js_urls = []  # documented in getter property

        #: Boolean flag, indicating whether the element should spawn
        #: its own logger, or use the class-specific logger.
        #: Can be set to *True* to allow for very fine-grained logging.
        #: In most cases, it is fine to leave it at the default (*False*)
        self.instance_level_logging: bool = instance_level_logging

        #: A :class:`~.QueuedLoggingInterface`, offering logging
        #: through the methods *debug*, *info*, *warning*, *error*,
        #: *exception*, and *log*.
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)

    @property
    def showif(self) -> dict:
        """
        dict: Conditions that have to be met for the element to be shown.

        The showif dictionary can contain multiple conditions as key-
        value-pairs. The element will only be shown, if *all* conditions
        are met. You can use all names that show up in the main dataset.
        That includes:

        * The names of all input elements that were shown before the
          current page
        * The names of all input elements *on* the current page
        * The experiment metadata, including *exp_condition*,
          *exp_start_time*, and more. See :attr:`.Experiment.metadata`

        .. note::
            If you wish to implement more sophisticated conditions (e.g.
            linking conditions with 'or' instead of 'and'), you can
            do so by using if-statements in an *on_first_show* or
            *on_each_show* page-hook.

            Those conditions will not work for elements on the same page
            though. If you want to create complex showif conditions
            depending on elements on the same page, you have to
            implement them in JavaScript yourself. See :meth:`.add_js`
            and :class:`.JavaScript` for information on how to add
            JavaScript.

        Examples:

            This is a simple showif based on experiment condition. The
            text element in this example will only be shown to subjects
            in the condition "one"::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    exp.condition = al.random_condition("one", "two")

                @exp.member
                class MyPage(al.Page):
                    name = "my_page"

                    def on_exp_access(self):
                        self += al.Text("This is text", showif={"exp_condition": "one"})

            This is a more complex condition using the hook method. The
            text element on *page2* will only be show to subjects, if
            they spent more than 20 seconds on *page1*::

                import alfred3 as al
                exp = al.Experiment()
                exp += al.Page(name="page1")

                @exp.member
                class SecondPage(al.Page):
                    name = "page2"

                    def on_first_show(self):
                        if sum(self.exp.page1.durations) > 20:
                            self += al.Text("This is text")

        See Also:
            Page hooks

        Todo:
            * Put link to page hooks explanation here.

        """
        return self._showif

    @showif.setter
    def showif(self, value: dict):
        if not isinstance(value, dict):
            raise TypeError("Showif must be of type 'dict'.")
        self._showif = value

    @property
    def converted_width(self) -> List[str]:
        """
        list: List of bootstrap column widths at different screen sizes.

        Converted from :attr:`.width`.
        """
        if self.width == "narrow":
            return ["col-12", "col-sm-6", "col-md-3"]
        elif self.width == "medium":
            return ["col-12", "col-sm-9", "col-md-6"]
        elif self.width == "wide":
            return ["col-12", "col-md-9"]
        elif self.width == "full":
            return ["col-12"]

    @property
    def width(self) -> str:
        """str: Element width"""
        return self._width

    @width.setter
    def width(self, value):
        if value is None:
            self._width = None
        elif value not in ["narrow", "medium", "wide", "full"]:
            raise ValueError(f"'{value}' is not a valid width.")
        self._width = value

    @property
    def position(self) -> str:
        """
        str: Position of the whole element on the page.

        Determines the element position, when an element is *not*
        full-width.
        """
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
    def font_size(self) -> int:
        """int: Font size"""
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = fontsize_converter(value)

    @property
    def element_width(self) -> str:
        """
        str: Returns a string of column width definitions.

        **Manually setting the width**

        The element width list can contain up to 5 width definitions,
        specified as integers from 1 to 12. The integers refer to the
        five breakbpoints in `Bootstrap 4's 12-column-grid system`_, i.e.
        [xs, sm, md, lg, xl]::

            >>> element = Element()
            >>> element.element_width = [12, 8, 8, 7, 6]
            element.element_width
            "col-12 col-sm-8 col-md-8 col-lg-7 col-xl-6"

        **Width resultion order**

        If there is no width defined for a certain screen size,
        the next smaller entry is used. For example, the following
        definition will lead to full width on extra small screens
        and 8/12 widths on all larger widths::

            element = Element()
            element.element_width = [12, 8]

        To make an element full-width on extra small and small
        screens and half-width on medium, large and extra large
        screens, follow this example::

            element = Element()
            element.element_width = [12, 12, 6]

        """
        if self.width is not None:
            return " ".join(self.converted_width)

        width = self._element_width if self._element_width is not None else ["col-12"]
        if self.experiment.config.getboolean("layout", "responsive", fallback=True):
            return " ".join(width)
        else:
            return width[0]

    @element_width.setter
    def element_width(self, value: List[int]):
        try:
            for v in value:
                if not isinstance(v, int):
                    raise TypeError("Element width must be set as a list of integers.")
        except TypeError:
            raise TypeError("Element width must be set as a list of integers.")
        self._element_width = value

    @property
    def name(self) -> str:
        """
        str: Unique identifier for the element.

        The element name will be used to identify the corresponding
        input in the final dataset.
        """
        return self._name

    @name.setter
    def name(self, name):
        if name is None:
            self._name = None

        elif name is not None:
            check_name(name)

        self._name = name

    @property
    def should_be_shown(self) -> bool:
        """
        bool: Boolean, indicating whether the element is meant to be shown.

        Evaluates all *showif* conditions. Can be set manually.
        Returns *False*, if the element's parent
        page should not be shown.
        """
        cond1 = self._should_be_shown
        cond2 = all(self._evaluate_showif())
        cond3 = self.page.should_be_shown
        return cond1 and cond2 and cond3

    @should_be_shown.setter
    def should_be_shown(self, b: bool):
        if not isinstance(b, bool):
            raise TypeError("should_be_shown must be an instance of bool")
        self._should_be_shown = b

    @property
    def section(self):
        """The direct parent section of this element's page."""
        return self.page.section

    @property
    def tree(self) -> str:
        """
        str: String, giving the exact position in the experiment.

        The tree is composed of the names of all sections
        and the element's page dots. Example for an element that belongs
        to a page "hello_world" that was added directly to the experiment::

            _root._content.hello_world

        ``_root`` and ``_content`` are basic sections that alfred always
        includes in an experiment.

        """
        return self.page.tree

    @property
    def short_tree(self) -> str:
        """
        str: String, giving the exact position in the experiment.

        This version of the tree omits the ``_root._content`` part that
        is the same for all elements.
        """

        return self.tree.replace("_root._content.", "")

    @property
    def css_code(self) -> List[Tuple[int, str]]:
        """List[tuple]: A list of tuples, which contain a priority and CSS code."""
        return self._css_code

    @property
    def css_urls(self) -> List[Tuple[int, str]]:
        """List[tuple]: A list of tuples, which contain a priority and an url pointing
        to CSS code."""
        return self._css_urls

    @property
    def js_code(self) -> List[Tuple[int, str]]:
        """List[tuple]: A list of tuples, which contain a priority and Javascript."""
        return self._js_code

    @property
    def js_urls(self) -> List[Tuple[int, str]]:
        """List[tuple]: A list of tuples, which contain a priority and an url pointing
        to JavaScript."""
        return self._js_urls

    @property
    def template_data(self) -> dict:
        """
        dict: Dictionary of data to be passed on to jinja templates.

        When deriving a new element class, you will often want to
        redefine this property to add template data. When doing so,
        remember to retrieve the basic template data with ``super()``::

            import alfred3 as al

            class NewElement(al.Element):

                @property
                def template_data(self):
                    d = super().template_data
                    d["my_value"] = "this is my value"

                    return d    # don't forget to return the dictionary!

        The call ``super().template_data`` applies the parent classes
        code to the current object. That way, you only need to define
        values that differ from the parent class.

        .. note::
            Be aware that, by default, the same template data will be
            passed to the respective templates when rendering
            :attr:`.inner_html` / :attr:`.element_template` and
            :attr:`.web_widget` / :attr:`.base_template`.

        """
        d = {}
        d["css_class_element"] = self.css_class_element
        d["css_class_container"] = self.css_class_container
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
            list: A list of booleans, indicating for each condition,
            whether it is met or not.
        """

        if self.showif:
            conditions = []
            for name, condition in self.showif.items():

                # skip current page (showifs for current pages are checked elsewhere)
                if name in self.page.all_input_elements:
                    continue

                val = self.exp.data_manager.flat_session_data[name]
                conditions.append(condition == val)

            return conditions
        else:
            return [True]

    def _activate_showif_on_current_page(self):
        """Adds JavaScript to self for dynamic showif functionality."""
        pg = self.page.all_input_elements
        on_current_page = dict([cond for cond in self.showif.items() if cond[0] in pg])

        if on_current_page:

            t = jinja_env.get_template("showif.js.j2")
            js = t.render(showif=on_current_page, element=self.name)
            self.js_code.append((7, js))
            self._showif_on_current_page = True

    # Public methods start here ----------------------------------------

    def added_to_experiment(self, experiment):
        """
        Tells the element that it was added to an experiment.

        The experiment is made available to the element, and the
        element's logging interface initializes its experiment-specific
        logging.

        This is also the place where the element's name is checked for
        experiment-wide uniqueness.

        Args:
            experiment: The alfred experiment to which the element was
                added.

        """

        if self.name in experiment.root_section.all_updated_elements:
            raise AlfredError(f"Element name '{self.name}' is already present in the experiment.")

        if self.name in experiment.data_manager.flat_session_data:
            raise AlfredError(f"Element name '{self.name}' conflicts with a protected name.")

        self.experiment = experiment
        self.exp = experiment
        self.log.add_queue_logger(self, __name__)

    def added_to_page(self, page):
        """
        Tells the element that it was added to a page.

        The page and the experiment are made available to the element.

        Args:
            page: The page to which the element was added.

        """
        from . import page as pg

        if not isinstance(page, pg.PageCore):
            raise TypeError()

        self.page = page
        if self.name is None:
            self.name = self.page.generate_element_name(self)

        if self.page.experiment and not self.experiment:
            self.added_to_experiment(self.page.experiment)

    def _prepare_web_widget(self):
        """
        Wraps :meth:`.prepare_web_widget` to allow for additional, generic
        preparations that are the same for all elements.

        This is useful, because :meth:`.prepare_web_widget` is often
        redefined in derived elements.
        """
        self._activate_showif_on_current_page()
        self.prepare_web_widget()

    def prepare_web_widget(self):
        """
        Hook for computations for preparing an element's web widget.

        This method is supposed to be overridden by derived elements if
        necessary.
        """
        pass

    # Magic methods start here -----------------------------------------

    def __str__(self):
        return f"{type(self).__name__}(name: '{self.name}')"

    def __repr__(self):
        return self.__str__()

    # abstract attributes start here -----------------------------------

    @property
    def inner_html(self) -> str:
        """
        Renders the element template :attr:`~.element_template`.

        Hands over the data returned by :attr:`~.template_data`, renders
        the template and returns the resulting html code.

        If no `element_template` is defined, `None` is returned. Usually,
        the inner html gets placed into the higher-level
        :attr: `.base_template`, when :attr:`Element.web_widget` gets called.

        Returns:
            str: Inner html code for this element.
        """
        if self.element_template is not None:
            return self.element_template.render(self.template_data)
        else:
            return None
    
    def render_inner_html(self, template_data: dict) -> str:
        return self.element_template.render(template_data)

    @property
    def web_widget(self) -> str:
        """
        The element's rendered html code for display on a page.

        This is done by rendering the
        :attr:`~.base_template` with the :attr:`~.template_data`
        and injecting the :attr:`~.inner_html` into it.

        Returns:
            str: The full html code for this element.
        """
        d = self.template_data
        d["html"] = self.render_inner_html(d)
        return self.base_template.render(d)

    @property
    def css_class_element(self) -> str:
        """
        Returns the name of the element's CSS class.

        On the webpage generated by alfred3, all elements reside in some
        sort of container which has a CSS class of the element's
        *css_class_element*. The name is composed as the element's class
        name, followed by ``-element``.

        Examples:

            This is a simplified illustration of the html structure of
            a text element. Let's say, the element was instantiated
            with the name "example_text". The element's *css_class_element*
            will be *Text-element*:

                >>> import alfred3 as al
                >>> ex = Text("This is an example", name="example_text")
                >>> ex.css_class_element
                Text-element

            The html code generated by this element is structured as
            follows

            .. code-block:: html

                <div class="Text-element-container" id="example_text-container">
                  ...
                  <div class="Text-element" id="example_text">
                    <p>This is an example</p>
                  </div>
                  ...
                </div>

            Note that the element receives two CSS classes and two IDs,
            one each for the outer container and one for the innermost
            layer. The outer container includes the element's base
            template (e.g. *Element.html*, or *LabelledElement.html*),
            while the inner layer includes the specific element-
            template (e.g. *TextElement.html*).

        """
        return f"{type(self).__name__}-element"

    @property
    def css_class_container(self) -> str:
        """
        str: Returns the name the element container's CSS class.

        The class can be used for CSS styling.

        See Also:
            See :attr:`.css_class_element` for details.
        """
        return f"{self.css_class_element}-container"

    def add_css(self, code: str, priority: int = 10):
        """
        Adds CSS to the element.

        This is most useful when writing new elements. To simply add
        element-related CSS code to a page, usually the :class:`.CSS`
        element is a better choice.

        Args:
            code: Css code
            priority: Can be used to influence the order in which code
                is added to the page. Sorting is ascending, i.e. the
                lowest numbers appear closest to the top of the page.

        See Also:
            * The :class:`.Style` element can be used to add generic CSS
              code to a page.
            * See :attr:`.Element.css_class_element` and
              :attr:`.Element.css_class_container` for information on
              element CSS classes and IDs.

        """
        self._css_code.append((priority, code))

    def add_js(self, code: str, priority: int = 10):
        """
        Adds Javascript to the element.

        This is most useful when writing new elements. To simply add
        element-related JavaScript code to a page, usually the
        :class:`.JavaScript` element is a better choice.

        Args:
            code: Css code
            priority: Can be used to influence the order in which code
                is added to the page. Sorting is ascending, i.e. the
                lowest numbers appear closest to the top of the page.

        See Also:
            * The :class:`.JavaScript` element can be used to add generic
              JavsScript code to a page.
            * See :attr:`.Element.css_class_element` and
              :attr:`.Element.css_class_container` for information on
              element CSS classes and IDs.

        """
        self._js_code.append((priority, code))


@dataclass
class _RowCol:
    """
    Just a little helper for handling columns inside a Row.

    :meta private:
    """

    breaks: str
    vertical_position: str
    element: Element
    id: str


class Row(Element):
    """
    Allows you to arrange up to 12 elements in a row.

    The row will arrange your elements using Bootstrap 4's grid system
    and breakpoints, making the arrangement responsive to different
    screen sizes. You can customize the behavior of the row for five
    different screen sizes (Bootstrap 4's default break points) with
    the width attributes of its layout attribute.

    If you don't specify breakpoints manually via the *layout* attribute,
    the columns will default to equal width and wrap on breakpoints
    automatically.

    Args:
        elements: The elements that you want to arrange in a row.
        valign_cols: List of vertical column alignments. Valid values
            are 'auto' (default), 'top', 'center', and 'bottom'. The
            elements of the list correspond to the row's columns. See
            :attr:`.RowLayout.valign_cols`
        elements_full_width: A switch, telling the row whether you wish
            it to resize all elements in it to full-width (default: True).
            This switch exists, because some elements might default to
            a smaller width, but when using them in a Row, you usually
            want them to span the full width of their column.
        name, showif, height, **kwargs: Passed on to the base class
            :class:`.Element`


    Notes:
        * CSS-class: row-element

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

    Examples:

        A minimal experiment with a row::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    el1 = al.Text("text")
                    el2 = al.TextEntry(toplab="lab", name="example")

                    self += al.Row(el1, el2)

        The arrangement will look like this::

            |=========|========|
            |   el1   |  el2   |
            |=========|========|

    """

    element_template = jinja_env.get_template("Row.html.j2")

    def __init__(
        self,
        *elements: Element,
        valign_cols: List[str] = None,
        elements_full_width: bool = True,
        height: str = "auto",
        name: str = None,
        showif: dict = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(name=name, showif=showif, height=height, **kwargs)

        #: List of the elements in this row
        self.elements: list = elements

        #: An instance of :class:`.RowLayout`,
        #: used for layouting. You can use this attribute to finetune
        #: column widths via the width attributes
        #: (e.g. :attr:`.RowLayout.width_xs`)
        self.layout = RowLayout(ncols=len(self.elements), valign_cols=valign_cols)

        #: If *True*, all elements will take up the full horizontal
        #: space of their column, regardless of the element's
        #: :attr:`.Element.element_width` and :attr:`.Element.width`
        #: attributes.
        self.elements_full_width: bool = elements_full_width

    def added_to_page(self, page):
        # docstring inherited
        super().added_to_page(page)

        for element in self.elements:
            if element is None:
                continue
            element.should_be_shown = False
            page += element

            if self.elements_full_width:
                element.width = "full"

    def _prepare_web_widget(self):
        # docstring inherited
        for element in self.elements:
            element.prepare_web_widget()

        super()._prepare_web_widget()

    @property
    def _cols(self) -> Iterator:
        """Yields preprocessed ``_RowCol`` columns ."""
        for i, element in enumerate(self.elements):
            col = _RowCol(
                breaks=self.layout.col_breaks(col=i),
                vertical_position=self.layout.valign_cols[i],
                element=element,
                id=f"{self.name}_col{i+1}",
            )
            yield col

    @property
    def template_data(self):
        # docstring inherited
        d = super().template_data
        d["columns"] = self._cols
        d["name"] = self.name
        return d


class Stack(Row):
    """
    Stacks multiple elements on top of each other.

    Stacks are intended for use in Rows. They allow you to flexibly
    arrange elements in a grid.

    Args:
        *elements: The elements to stack.
        **kwargs: Keyword arguments that are passend on to the parent
            class :class:`.Row`.

    Notes:
        * CSS-class: ``stack-element``

        * Html element id: ``elid-<name>`` (<name> is the
          :attr:`.Element.name` attribute, defined at initialization.)

    Examples:

        A minimal experiment with a stack in a row::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    el1 = al.Text("text")
                    el2 = al.TextEntry(toplab="lab", name="example")
                    el3 = al.Text("long text")

                    self += al.Row(al.Stack(el1, el2), el3)

        The arrangement will look like this::

            |=========|========|
            |   el1   |        |
            |=========|  el3   |
            |   el2   |        |
            |=========|========|

    """

    def __init__(self, *elements: Element, **kwargs):
        """Constructor method."""
        super().__init__(*elements, **kwargs)
        self.layout.width_xs = [12 for element in elements]


class VerticalSpace(Element):
    """
    The easiest way to add vertical space to a page.

    Args:
        space: Desired space in any unit that is understood by a CSS
            margin (e.g. em, px, cm). Include the unit (e.g. '1em').

    Notes:
        CSS-class: vertical-space-element

    Examples:

        Example of vertical space added between two text elements::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Text("Element 1")
                    self += al.VerticalSpace("100px")
                    self += al.Text("Element 2")

    """

    def __init__(self, space: str = "1em"):
        """Constructor method."""
        super().__init__()
        self.space = space

    @property
    def web_widget(self):
        """:meta private: (documented at :class:`.Element`)"""
        # documented at baseclass
        return f"<div class='vertical-space-element' style='margin-bottom: {self.space};'></div>"


class Style(Element):
    """
    Adds CSS code to a page.

    CSS styling can be used to change the appearance of page or
    individual elements.

    Notes:
        A style is added to a specific page, and thus only affects the
        layout of that page. To change the appearance of the whole
        experiment, you can define your styles in a .css file in your
        experiment directory and reference it in the *config.conf* in
        the option *style* of the section *layout*.

    See Also:
        * How to reference a CSS file in the *config.conf*
        * See :attr:`.Element.css_class_element` and
          :attr:`.Element.css_class_container` for information on
          element CSS classes and IDs.
        * The method :meth:`.Element.add_css` can be used to add CSS
          to a specific element.

    Todo:
        * Insert reference

    """

    web_widget = None
    should_be_shown = False

    def __init__(self, code: str = None, url: str = None, path: str = None, priority: int = 10):
        """Constructor method"""
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
        """:meta private: (documented at :class:`.Element`)"""
        if self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def css_urls(self):
        """:meta private: (documented at :class:`.Element`)"""
        if self.url:
            return [(self.priority, self.url)]
        else:
            return []


class HideNavigation(Style):
    """
    Removes the forward/backward/finish navigation buttons from a page.

    See Also:
        * Using :class:`.JumpButtons` and :class:`.JumpList`, you can add
          custom navigation elements to a page.

        * By defining the :meth:`.Page.custom_move` method on a page,
          you can implement highly customized movement behavior.
    """

    def __init__(self):
        """Constructor method"""
        super().__init__()
        self.code = "#page-navigation {display: none;}"


class JavaScript(Element):
    """
    Adds JavaScript to a page.

    Javascript can be used to implement dynamic behavior on the client
    side.

    See Also:
        * See :attr:`.Element.css_class_element` and
          :attr:`.Element.css_class_container` for information on
          element CSS classes and IDs.
        * The method :meth:`.Element.add_js` can be used to add JS
          to a specific element.

    Todo:
        * Insert reference
    """

    web_widget = None
    should_be_shown = False

    def __init__(self, code: str = None, url: str = None, path: str = None, priority: int = 10):
        """Constructor method"""
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
        """:meta private: (documented at :class:`.Element`)"""
        if self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def js_urls(self):
        """:meta private: (documented at :class:`.Element`)"""
        if self.url:
            return [(self.priority, self.url)]
        else:
            return []


class WebExitEnabler(JavaScript):
    """
    Removes the "Do you really want to leave?" popup upon closing a page.

    By default, subjects are asked to confirm their desire to leave a
    running experiment. You can turn off this behavior by adding this
    element to a page.

    """

    def __init__(self):
        """Constructor method"""
        code = "$(document).ready(function(){glob_unbind_leaving();});"
        super().__init__(code=code, priority=10)


class Html(Element):
    """
    Displays html code on a page.

    Args:
        html: Html to be displayed.
        path: Filepath to a file with html code (relative to the
            experiment directory).
        **kwargs: Keyword arguments passed to the parent class
            :class:`Element`.

    Notes:
        * CSS-class: html-element

        This works very similar to :class:`.Text`. The most notable
        difference is that the *Text* element expects markdown, and
        therefore generally renders input text in a ``<p>`` tag. This
        is not always desirable for custom html, because it adds a
        margin at the bottom of the text.

        The *Html* element renders neither markdown, nor emoji shortcodes.

    Examples:
        Adding a simple div to the experiment::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Html("<div id='mydiv'>Text in div</div>")

    """

    element_template = jinja_env.get_template("TextElement.html.j2")

    def __init__(
        self,
        html: str = None,
        path: Union[Path, str] = None,
        **element_args,
    ):

        """Constructor method."""
        super().__init__(**element_args)

        self.html_code = html if html is not None else ""
        self.path = path

        if self._html_code and self.path:
            raise ValueError("You can only specify one of 'html' and 'path'.")

    @property
    def html_code(self) -> str:
        """str: The element's html code"""
        if self.path:
            return self.experiment.subpath(self.path).read_text()
        else:
            return self._html_code

    @html_code.setter
    def html_code(self, html):
        self._html_code = html

    @property
    def template_data(self) -> dict:
        """:meta private: (documented at :class:`.Element`)"""
        d = super().template_data
        d["text"] = self.html_code

        return d


class Text(Element):
    """Displays text.

    You can use `GitHub-flavored Markdown`_ syntax and common
    `emoji shortcodes`_ . Additionally, you can use raw html for
    advanced formatting.

    Args:
        text: Text to be displayed.
        path: Filepath to a textfile (relative to the experiment
            directory).
        width: Element width. Usage is the same as in
            :class:`Element`, but the Text element uses its own
            specific default, which ensures good readability in
            most cases on different screen sizes.
        emojize: If True (default), emoji shortcodes in the text will
            be converted to unicode (i.e. emojis will be displayed).
        **kwargs: Keyword arguments passed to the parent class
            :class:`Element`.

    Notes:
        CSS-class: text-element

    Examples:
        A simple text element, including a 😊 (``:blush:``) emoji added
        to a page::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Text("This is text :blush:")


    .. _GitHub-flavored Markdown: https://guides.github.com/features/mastering-markdown/
    .. _emoji shortcodes: https://www.webfx.com/tools/emoji-cheat-sheet/
    """

    element_template = jinja_env.get_template("TextElement.html.j2")

    def __init__(
        self,
        text: str = None,
        path: Union[Path, str] = None,
        width: str = None,
        emojize: bool = True,
        **kwargs,
    ):

        """Constructor method."""
        super().__init__(width=width, **kwargs)

        self._text = text if text is not None else ""

        #: pathlib.Path: Path to a textfile, if specified in the init
        self.path: Path = Path(path) if path is not None else path

        #: bool: Boolean flag, indicating whether emoji shortcodes should be
        #: interpreted
        self.emojize: bool = emojize

        if self._text and self.path:
            raise ValueError("You can only specify one of 'text' and 'path'.")

    @property
    def text(self) -> str:
        """str: The text to be displayed"""
        if self.path:
            return self.experiment.subpath(self.path).read_text()
        else:
            return self._text

    def render_text(self) -> str:
        """
        Renders the markdown and emoji shortcodes in :attr:`.text`

        Returns:
            str: Text rendered to html code
        """

        if self.emojize:
            text = emojize(self.text, use_aliases=True)
        else:
            text = self.text
        return cmarkgfm.github_flavored_markdown_to_html(text)

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def element_width(self) -> str:
        """:meta private: (documented at :class:`.Element`)"""
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
        """:meta private: (documented at :class:`.Element`)"""
        d = super().template_data
        d["text"] = self.render_text()

        return d


class Hline(Element):
    """A simple horizontal line."""

    inner_html = "<hr>"


class CodeBlock(Text):
    """
    A convenience element for displaying highlighted code.

    Args:
        text: The code to be displayed.
        path: path: Filepath to a textfile (relative to the experiment
            directory) from which to read code.
        lang: The programming language to highlight [#lang]_ . Defaults
            to 'auto', which tries to auto-detect the right language.
        **kwargs: Keyword arguments are passed on to the parent elements
            :class:`.Text` and :class:`.Element`

    .. [#lang] See https://prismjs.com/index.html#supported-languages
        for an overview of possible language codes. Note though that
        we may not support all possible languages.

    """

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
        """:meta private: (documented at :class:`.Element`)"""
        if self.path:
            text = self.experiment.subpath(self.path).read_text()

            code = f"```{self.lang}\n{text}\n```"
            return code
        else:
            code = f"```{self.lang}\n{self._text}\n```"
            return code


class Label(Text):
    """
    A utility class, serving as label for other elements.

    """

    def __init__(self, text, width="full", **kwargs):
        super().__init__(text=text, width=width, **kwargs)

        #: RowLayout: Layouting facility for controlling the column
        #: breaks and vertical alignment of the label. Gets set by
        #: :class:`.LabelledElement` automatically.
        self.layout: RowLayout = None

        #: Tells the label which column of the :attr:`.layout` it is
        self.layout_col: int = None

    @property
    def col_breaks(self) -> str:
        """The label's breakpoints for diferent screen sizes."""
        return self.layout.col_breaks(self.layout_col)

    @property
    def vertical_alignment(self) -> str:
        """The label's vertical alignment"""
        return self.layout.valign_cols[self.layout_col]


class LabelledElement(Element):
    """
    An intermediate Element class which provides support for labels.

    This class is used as a base class for all elements that come
    equipped with labels.

    Args:
        toplab, leftlab, rightlab, bottomlab: String or instance of
            :class:`.Label`, which will be used to label the element.
        layout: A list of integers, specifying the allocation of
            horizontal space between leftlab, main element widget and
            rightlab. Uses Bootstraps 12-column-grid, i.e. you can
            choose integers between 1 and 12.

    """

    base_template = jinja_env.get_template("LabelledElement.html.j2")

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
            self._input_col = 1
            self._layout = RowLayout(ncols=3)
            self._layout.width_sm = layout if layout is not None else [2, 8, 2]
        elif leftlab:
            # for accessing the right col in layout.col_breaks for the input field
            self._input_col = 1
            self._layout = RowLayout(ncols=2)
            self._layout.width_sm = layout if layout is not None else [3, 9]
        elif rightlab:
            # for accessing the right col in layout.col_breaks for the input field
            self._input_col = 0
            self._layout = RowLayout(ncols=2)
            self._layout.width_sm = layout if layout is not None else [9, 3]
        else:
            # for accessing the right col in layout.col_breaks for the input field
            self._input_col = 0
            self._layout = RowLayout(ncols=1)
            self._layout.width_sm = [12]

        self._layout.valign_cols = ["center" for el in range(self._layout.ncols)]

        self.toplab = toplab
        self.leftlab = leftlab
        self.rightlab = rightlab
        self.bottomlab = bottomlab

    def added_to_page(self, page):
        """:meta private: (documented at :class:`.Element`)"""
        super().added_to_page(page)

        for lab in ["toplab", "leftlab", "rightlab", "bottomlab"]:
            if getattr(self, lab):
                getattr(self, lab).name = f"{self.name}_{lab}"

    def added_to_experiment(self, experiment):
        """:meta private: (documented at :class:`.Element`)"""
        super().added_to_experiment(experiment)
        self._layout.responsive = self.experiment.config.getboolean("layout", "responsive")

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
        """.Label: Label above of the main element widget."""
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
        """.Label: Label below of the main element widget."""
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
        """.Label: Label to the left of the main element widget."""
        return self._leftlab

    @leftlab.setter
    def leftlab(self, value: str):
        if isinstance(value, Label):
            self._leftlab = value
            self._leftlab.layout = self._layout
            self._leftlab.layout_col = 0
        elif isinstance(value, str):
            self._leftlab = Label(text=value, align="right")
            self._leftlab.layout = self._layout
            self._leftlab.layout_col = 0
        else:
            self._leftlab = None

    @property
    def rightlab(self):
        """.Label: Label to the right of the main element widget."""
        return self._rightlab

    @rightlab.setter
    def rightlab(self, value: str):
        if isinstance(value, Label):
            self._rightlab = value
            self._rightlab.layout = self._layout
            self._rightlab.layout_col = self._input_col + 1
        elif isinstance(value, str):
            self._rightlab = Label(text=value, align="left")
            self._rightlab.layout = self._layout
            self._rightlab.layout_col = self._input_col + 1
        else:
            self._rightlab = None

    @property
    def labels(self) -> str:
        """str: Returns the labels in a single, nicely formatted string."""

        labels = []
        if self.toplab:
            labels.append(f"toplab: '{self.toplab.text}'")
        if self.leftlab:
            labels.append(f"leftlab: '{self.leftlab.text}'")
        if self.rightlab:
            labels.append(f"rightlab: '{self.rightlab.text}'")
        if self.bottomlab:
            labels.append(f"bottomlab: '{self.bottomlab.text}'")

        if labels:
            return ", ".join(labels)

    @property
    def template_data(self):
        """:meta private: (documented at :class:`.Element`)"""
        d = super().template_data
        d["toplab"] = self.toplab
        d["leftlab"] = self.leftlab
        d["rightlab"] = self.rightlab
        d["bottomlab"] = self.bottomlab
        d["input_breaks"] = self._layout.col_breaks(col=self._input_col)
        d["input_valign"] = self._layout.valign_cols[self._input_col]
        return d


class ProgressBar(LabelledElement):
    """
    Displays a progress bar.

    Args:
        progress: Can be either "auto", or a number between 0 and 100.
            If "auto", the progress is calculated from the current
            progress of the experiment. If a number is supplied, that
            number will be used as the progress to be displayed.
        bar_height: Height of the progress bar. Supply a string with
            unit, e.g. "6px".
        show text: Indicates, whether the progress bar should include
            text with the current progress.
        striped: Indicates, whether the progress bar shoulb be striped.
        style: Determines the color of the progress bar. Possible values
            are "primary", "secondary", "info", "success", "warning",
            "danger", "light", "dark".
        animated: Determines, whether a striped progress bar should be
            equipped with an animation.
        round: Determines, whether the corners of the progress bar
            should be round.

    See Also:
        See :attr:`.ExperimentSession.progress_bar` for more information
        on the experiment-wide progress bar.

    Notes:
        If the argument *show_text* is *True*, the text's appearance
        can be altered via CSS. It receives a class of
        ":attr:`.css_class_element`-text" and an id of
        ":attr:`.name`-text". You can use the method :meth:`.add_css`
        to append fitting CSS to the bar (see examples).

    Examples:

        Overriding the default experiment-wide progress bar::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp_session):
                exp_session.progress_bar = al.ProgressBar(show_text=True, bar_height="15px")

            exp += al.Page(name="example_page")

        Adding a progress bar as an element to a page::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Example(al.Page):
                name = "example_page"

                def on_exp_access(self):
                    self += al.ProgressBar()

        Altering the progress bar text's apperance, applied to the
        experiment-wide progress bar. Note that the experiment-wide
        progress bar *always* receives the name "*progress_bar_*"::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp):
                exp.progress_bar = al.ProgressBar(show_text=True, bar_height="15px")
                exp.progress_bar.add_css("#progress_bar_ {font-size: 12pt;}")

            exp += al.Page(name="example_page")

    """

    element_template = jinja_env.get_template("ProgressBarElement.html.j2")

    def __init__(
        self,
        progress: Union[str, float, int] = "auto",
        bar_height: str = "6px",
        show_text: bool = False,
        striped: bool = True,
        style: str = "primary",
        animated: bool = False,
        round_corners: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._progress_setting = progress

        if not isinstance(progress, (str, float, int)):
            raise TypeError

        self._progress: int = None
        self._bar_height: str = bar_height
        self._show_text: bool = show_text
        self._striped: bool = striped
        self._bar_style: str = style
        self._animated: bool = animated
        self._round_corners: bool = "border-radius: 0;" if round_corners == False else ""

    def added_to_experiment(self, exp):
        """:meta private: (documented at :class:`.Element`)"""
        super().added_to_experiment(exp)

        css = f".progress#{self.name}  {{height: {self._bar_height}; {self._round_corners}}}"
        self.add_css(code=css)

    def _prepare_web_widget(self):
        if self._progress_setting == "auto":
            self._progress = self._calculate_progress()
        elif isinstance(self._progress_setting, (int, float)):
            self._progress = self._progress_setting

        self.prepare_web_widget()

        try:
            self._activate_showif_on_current_page()
        except AttributeError as e:
            # special treatment for experiment-wide progress bar
            # because that one only has an experiment, no page
            if self.page is None and self.name == "progress_bar_":
                pass
            else:
                raise e

    def _calculate_progress(self) -> float:
        """
        Calculates the current progress.

        Returns:
            float: Current progress
        """
        n_el = 0
        for el in self.exp.root_section.all_input_elements.values():
            if el.should_be_shown:
                n_el += 1
            elif el.showif or el.page.showif or el.section.showif:
                n_el += 0.3

        n_pg = len(self.experiment.root_section.visible("all_pages"))
        shown_el = len(self.experiment.root_section.all_shown_input_elements)
        shown_pg = len(self.experiment.root_section.all_shown_pages)
        exact_progress = ((shown_el + shown_pg) / (n_el + n_pg)) * 100

        if not self.experiment.finished:
            return min(round(exact_progress, 1), 95)
        else:
            return 100

    @property
    def template_data(self):
        """:meta private: (documented at :class:`.Element`)"""
        d = super().template_data
        d["progress"] = self._progress
        d["show_text"] = self._show_text
        d["bar_height"] = self._bar_height
        d["bar_style"] = f"bg-{self._bar_style}"
        d["striped"] = "progress-bar-striped" if self._striped else ""
        d["animated"] = "progress-bar-animated" if self._animated else ""
        return d


class Alert(Text):
    """
    Allows the display of customized alerts.

    Args:
        text: Alert text
        category: Affects the appearance of alerts.
            Values can be: "info", "success", "warning", "primary",
            "secondory", "dark", "light", "danger".
        dismiss: Boolean parameter. If "True", AlertElement can be
            dismissed by a click. If "False", AlertElement is not
            dismissible. Default = "False"
        **element_args: Keyword arguments passed to the parent class
            :class:`TextElement`. Accepted keyword arguments are: name,
            font_size, align, width, position, showif,
            instance_level_logging.

    Examples:

        >>> import alfred3 as al
        >>> alert = al.AlertElement(text="Alert text", dismiss=True, name="al1")
        >>> alert
        Alert(name='al1')

    """

    element_template = jinja_env.get_template("AlertElement.html.j2")

    def __init__(
        self, text: str = "", category: str = "info", dismiss: bool = False, **element_args
    ):
        super().__init__(text=text, **element_args)
        self.category = category
        self.dismiss = dismiss

    @property
    def template_data(self):
        d = super().template_data
        d["category"] = self.category
        d["role"] = "alert"
        d["dismiss"] = self.dismiss

        return d


class InputElement(LabelledElement):
    """
    Base class for elements that allow data input.

    Args:
        toplab: String or instance of :class:`.Label`, which will be
            used to label the element. The other labels (leftlab,
            rightlab, bottomlab) are supported aswell. Specify them
            as keyword arguments, not positional arguments.
        force_input: If `True`, users can only progress to the next page
            if they enter data into this field. Note that a
            :class:`.NoValidationSection` or similar sections might
            overrule this setting. 
            
            A general, experiment-wide setting for force_input can be 
            placed in the config.conf (section "general"). That setting
            is used by default and can be overruled here for individual
            elements.
        default: Default value. Type depends on the element type.
        prefix: Prefix for the input field.
        suffix: Suffix for the input field.
        description: An additional description of the element. This will
            show up in the alfred-generated codebook. It has
            no effect on the display of the experiment, as it only
            serves as a descriptor for humans.
        no_input_corrective_hint: Hint to be displayed if force_input
            set to True and no user input registered. Defaults to the
            experiment-wide value specified in config.conf.
        **kwargs: Further keyword arguments are passed on to the
            parent classes :class:`.LabelledElement` and :class:`Element`.

    Notes:
        The InputElement does not have its own display. It is used only
        to inherit functionality.

    """

    #: Boolean flag, indicating whether the element's html template
    #: has a dedicated container for corrective hints. If *False*,
    #: corrective hints regarding this element will be placed in the
    #: general page-wide conainer for such hints.
    can_display_corrective_hints_in_line: bool = True

    def __init__(
        self,
        toplab: str = None,
        force_input: bool = None,
        default: Union[str, int, float] = None,
        prefix: Union[str, Element] = None,
        suffix: Union[str, Element] = None,
        description: str = None,
        disabled: bool = False,
        no_input_corrective_hint: str = None,
        **kwargs,
    ):
        super().__init__(toplab=toplab, **kwargs)

        #: Detailed description of this element to be added to the
        #: automatically generated codebook
        self.description = description

        self._input = ""
        self._force_input = force_input  # documented in getter property
        self._no_input_corrective_hint = no_input_corrective_hint
        self._default = default  # documented in getter property
        self._prefix = prefix  # documented in getter property
        self._suffix = suffix  # documented in getter property

        #: Flag, indicating whether corrective hints regarding
        #: this element should be shown.
        self.show_corrective_hints: bool = False

        #: A :class:`.MessageManager`, handling the corrective hints
        #: for this element.
        self.hint_manager = MessageManager(default_level="danger")

        #: A boolean flag, indicating whether the element is disabled
        #: A disabled input element is shown and displays its input
        #: value, but subjects cannot enter any data.
        self.disabled: bool = disabled

        if default is not None:
            self._input = default

        if self._force_input and (self._showif_on_current_page or self.showif):
            raise ValueError(f"Elements with 'showif's can't be 'force_input' ({self}).")

    def _prepare_web_widget(self):
        """:meta private: (documented at :class:`.Element`)"""
        super()._prepare_web_widget()

        try:
            self._prefix._prepare_web_widget()
        except AttributeError:
            pass

        try:
            self._suffix._prepare_web_widget()
        except AttributeError:
            pass

    @property
    def corrective_hints(self) -> Iterator[str]:
        """
        Shortcut for accessing the element's corrective hints.

        Yields:
            str: Corrective hint.
        """
        return self.hint_manager.get_messages()

    @property
    def debug_value(self) -> Union[str, None]:
        """
        Union[str, None]: Value to be used as a default in debug mode.

        This value is read from config.conf. Only used, if there is no
        dedicated default for this element.

        Notes:
            The property searches for an option of the form
            ``<element_class>_debug`` in the section *debug* of
            config.conf. If no option is found, the return value is
            *None*
        """
        name = f"{type(self).__name__}_default"
        return self.experiment.config.get("debug", name, fallback=None)

    @property
    def debug_enabled(self) -> bool:
        """
        bool: Boolean flag, indicating whether debug mode is enabled and
        default values should be set.
        """
        if self.experiment.config.getboolean("general", "debug"):
            if self.experiment.config.getboolean("debug", "set_default_values"):
                return True
        return False

    @property
    def default(self) -> Union[str, int, float]:
        """
        Union[str, int, float]: Default value of this element.

        The data type can vary, depending on the element.
        """
        if self._default is not None:
            return self._default
        elif self.debug_enabled:
            return self.debug_value
        else:
            return None

    @default.setter
    def default(self, value):
        self._default = value

    @property
    def force_input(self) -> bool:
        """
        bool: If *True*, subjects *must* fill this element to proceed.

        A general, experiment-wide setting for force_input can be placed
        in the config.conf (section "general").
        """
        if self._force_input is None:
            return self.exp.config.getboolean("general", "force_input")
        else:
            return self._force_input

    @force_input.setter
    def force_input(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("Force input must be a boolean value.")

        self._force_input = value

    @property
    def template_data(self) -> dict:
        """:meta private: (documented at :class:`.Element`)"""
        d = super().template_data
        d["default"] = self.default
        d["prefix"] = self.prefix
        d["suffix"] = self.suffix
        d["input"] = self.input
        d["disabled"] = self.disabled
        d["corrective_hints"] = list(self.corrective_hints)
        return d

    def validate_data(self) -> bool:
        """
        Method for validation of input to the element.

        Returns:
            bool: *True*, if the input is correct and subjects may
                proceed to the next page, *False*, if the input is not
                in the correct form.
        """
        if self.force_input and not self.input:
            self.hint_manager.post_message(self.no_input_hint)
            return False
        else:
            return True

    @property
    def no_input_hint(self) -> str:
        """
        str: Hint for subjects, if they left a *force_input* field empty.
        """
        if self._no_input_corrective_hint:
            return self._no_input_corrective_hint
        return self.default_no_input_hint

    @property
    def default_no_input_hint(self) -> str:
        """
        str: Default hint if subject input is missing in *force_entry* elements.

        This value is read from config.conf. Only used, if there is no
        dedicated :attr:`.no_input_hint` for this element.

        Notes:
            The property searches for an option of the form
            ``<element_class>_debug`` in the section *debug* of
            config.conf. If no option is found, the return value is
            "You need to enter something".
        """
        name = f"no_input{type(self).__name__}"
        return self.experiment.config.get("hints", name, fallback="You need to enter something.")

    @property
    def prefix(self):
        """
        Union[str, Element]: A string or element, serving as prefix.

        If the prefix is an element, the getter returns its
        :attr:`.Element.inner_html`. If it is a string, the getter
        returns the text, wrapped in an appropriate html container.
        """
        try:
            return self._prefix.inner_html
        except AttributeError:
            return self._render_input_group_text(self._prefix)

    @property
    def suffix(self):
        """
        Union[str, Element]: A string or element, serving as suffix.

        If the suffix is an element, the getter returns its
        :attr:`.Element.inner_html`. If it is a string, the getter
        returns the text, wrapped in an appropriate html container.
        """
        try:
            return self._suffix.inner_html
        except AttributeError:
            return self._render_input_group_text(self._suffix)

    def _render_input_group_text(self, text: str) -> str:
        if text is not None:
            return f"<div class='input-group-text'>{text}</div>"
        else:
            return None

    @property
    def input(self) -> str:
        """
        str: Subject input to this element.
        """
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    @property
    def data(self) -> dict:
        """
        dict: Dictionary of element data.

        Includes the subject :attr:`.input` and the element's
        :attr:`.codebook_data`.
        """
        data = {}
        data["value"] = self.input
        data.update(self.codebook_data)
        return {self.name: data}

    def set_data(self, d: dict):
        """
        Sets the :attr:`.input` data.

        Args:
            d: A dictionary with data.

        Notes:
            The *d* dictionary will usually be a dictionary of all data
            collected on a page.
        """
        if not self.disabled:
            try:
                self.input = d[self.name]
            except KeyError:
                self.log.debug(f"No data for {self} found in data dictionary. Moving on.")
                pass

    @property
    def codebook_data(self) -> dict:
        """
        dict: Information about the element in dictionary form.
        """

        from alfred3 import page

        data = {}
        data["name"] = self.name
        data["label_top"] = self.toplab.text if self.toplab is not None else ""
        data["label_left"] = self.leftlab.text if self.leftlab is not None else ""
        data["label_right"] = self.rightlab.text if self.rightlab is not None else ""
        data["label_bottom"] = self.bottomlab.text if self.bottomlab is not None else ""
        data["tree"] = self.short_tree
        data["page_title"] = self.page.title
        data["element_type"] = type(self).__name__
        data["force_input"] = self._force_input
        data["prefix"] = self._prefix
        data["suffix"] = self._suffix
        data["default"] = self.default
        data["description"] = self.description
        data["unlinked"] = True if isinstance(self.page, page.UnlinkedDataPage) else False
        return data

    def added_to_page(self, page):
        """:meta private: (documented at :class:`.Element`)"""
        from . import page as pg

        if not isinstance(page, pg.PageCore):
            raise TypeError()

        self.page = page
        if self.name is None:
            raise ValueError(f"{self} is not named. Input elements must be named")

        if self.page.experiment and not self.experiment:
            self.added_to_experiment(self.page.experiment)

        for fix in (self._prefix, self._suffix):
            try:
                fix.should_be_shown = False
                self.page += fix
            except AttributeError:
                pass


class Data(InputElement):
    """
    Data can be used to save data without any display.

    Example::

        Data(value="test", name="mydata")

    Args:
        value: The value that you want to save.
    """

    def __init__(self, value: Union[str, int, float], description: str = None, **kwargs):
        """Constructor method."""

        if kwargs.pop("variable", False):
            raise ValueError("'variable' is not a valid parameter. Use 'value' instead.")

        super().__init__(**kwargs)
        self.value = value
        self.description = description
        self.should_be_shown = False


class Value(Data):
    pass


class TextEntry(InputElement):
    """Provides a text entry field.

    Args:
        placeholder: Placeholder text, displayed inside the input field.
        **kwargs: Further keyword arguments that are passed on to the
            parent class :class:`InputElement`.

    """

    element_template = jinja_env.get_template("TextEntryElement.html.j2")

    def __init__(
        self,
        toplab: str = None,
        placeholder: str = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(toplab=toplab, **kwargs)

        self._placeholder = placeholder if placeholder is not None else ""

    @property
    def placeholder(self):
        return self._placeholder

    @property
    def template_data(self):
        d = super().template_data
        d["placeholder"] = self.placeholder
        return d

    @property
    def codebook_data(self):
        data = super().codebook_data
        data["prefix"] = self.prefix
        data["suffix"] = self.suffix
        data["placeholder"] = self.placeholder

        return data


class TextArea(TextEntry):
    element_template = jinja_env.get_template("TextAreaElement.html.j2")

    def __init__(self, toplab: str = None, nrows: int = 5, **kwargs):
        super().__init__(toplab=toplab, **kwargs)
        self.area_nrows = nrows

    @property
    def template_data(self):
        d = super().template_data
        d["area_nrows"] = self.area_nrows
        return d


class RegEntry(TextEntry):
    """
    Displays an input field, which only accepts inputs, matching a
    predefined regular expression.

    Args:
        pattern: Regular expression string to match with user input. We
            recommend that you use raw literal strings prefaced by 'r' 
            (see Examples). That removes the necessity for escaping some
            characters twice and thus makes the regular expression
            easier to read and write.
        match_hint: Hint to be displayed if the user input doesn't
            match with the regular expression.
        **kwargs, toplab: Keyword arguments that are passed on to the
            parent class :class:`.TextEntry`.

    Examples:
        
        Example for a RegEntry element that will match any input:

            >>> import alfred3 as al
            >>> regentry = al.RegEntry("Enter text here", pattern=r".*", name="reg1")
            >>> regentry
            RegEntry(name='reg1')

    """

    def __init__(self, toplab: str = None, pattern: str = r".*", match_hint: str = None, **kwargs):
        super().__init__(toplab=toplab, **kwargs)

        #: Compiled regular expression pattern to be matched on
        #: participant input to this element
        self.pattern: re.Pattern = re.compile(pattern)
        self._match_hint = match_hint # documented in getter property

    def validate_data(self):
        """:meta private: (documented at :class:`.InputElement`)"""
        if not self.should_be_shown:
            return True
        
        elif not self.force_input and self.input == "":
            return True
        
        elif not self.input:
            self.hint_manager.post_message(self.no_input_hint)
            return False
        
        elif not self.pattern.fullmatch(self.input):
            self.hint_manager.post_message(self.match_hint)
            return False

    @property
    def match_hint(self):
        """
        str: Hint to be displayed, if participant input does not match
        the provided pattern.
        """
        if self._match_hint:
            return self._match_hint
        else:
            return self.default_match_hint
    
    @property
    def default_match_hint(self) -> str:
        """
        str: Default match hint for this element, extracted from config.conf
        """
        name = f"match_{type(self).__name__}"
        return self.experiment.config.get("hints", name)
    
    @property
    def codebook_data(self) -> dict:
        """:meta private: (documented at :class:`.InputElement`)"""
        d = super().codebook_data
        d["regex_pattern"] = self.pattern.pattern
        return d


class NumberEntry(TextEntry):
    """
    Displays an input field which only accepts numerical input.

    Args:
        decimals: Accepted number of decimals (0 as default).
        min: Minimum accepted entry value.
        max: Maximum accepted entry value.
        decimal_signs: Tuple of accepted decimal signs. Defaults to 
            (",", "."), i.e. by default, both a comma and a dot are
            interpreted as decimal signs.
        match_hint: Specialized match hint for this element. You can 
            use the placeholders ``${min}``, ``${max}`` ``${ndecimals}``,
            and ``${decimal_signs}``. To customize the match hint for 
            all NumberEntry elements, change the respective setting
            in the config.conf.
        **kwargs, toplab: Further keyword arguments that are passed on 
            to the parent class :class:`TextEntry`.

    Examples:

        >>> import alfred3 as al
        >>> numentry = al.NumberEntry("enter here", name="num1")
        >>> numentry
        NumberEntry(name='num1')

    """

    def __init__(
        self,
        toplab: str = None,
        ndecimals: int = 0,
        min: Union[int, float] = None,
        max: Union[int, float] = None,
        decimal_signs: Union[str, tuple] = (",", "."),
        match_hint: str = None,
        **kwargs,
    ):
        super().__init__(toplab=toplab, **kwargs)

        self.ndecimals: int = ndecimals # documented in getter property
        self.decimal_signs: Tuple[str] = decimal_signs # documented in getter property
        self.min = min # documented in getter property
        self.max = max # documented in getter property
        self._match_hint = match_hint # documented in getter property
    
    @property
    def ndecimals(self) -> int:
        """int: Number of allowed decimal places."""
        return self._ndecimals
    
    @ndecimals.setter
    def ndecimals(self, value: int):
        if not isinstance(value, int) or not value >= 0:
            raise ValueError("Number of decimals must be an integer >= 0.")
        else:
            self._ndecimals = value
    
    @property
    def decimal_signs(self) -> Union[str, tuple]:
        """Union[str, tuple]: Interpreted decimal signs."""
        return self._decimal_signs
    
    @decimal_signs.setter
    def decimal_signs(self, value: Union[str, tuple]):
        msg = "Decimals signs must be a string or a tuple of strings."
        if not isinstance(value, (str, tuple)):
            raise ValueError(msg)
        
        if isinstance(value, tuple):
            for val in value:
                if not isinstance(val, str):
                    raise ValueError(msg)
        
        self._decimal_signs = value

    @property
    def min(self) -> Union[int, float]:
        """Minimum value that is accepted by this element."""
        return self._min
    
    @min.setter
    def min(self, value: Union[int, float]):
        if value is None:
            self._min = None
        elif not isinstance(value, (int, float)):
            raise ValueError("Minimum must be a number.")
        else:
            self._min = value
    
    @property
    def max(self) -> Union[int, float]:
        """Maximum value that is accepted by this element."""
        return self._max
    
    @max.setter
    def max(self, value: Union[int, float]):
        if value is None:
            self._max = None
        elif not isinstance(value, (int, float)):
            raise ValueError("Maximum must be a number.")
        else:
            self._max = value
    
    @property
    def match_hint(self):
        """
        str: Hint to be displayed, if participant input does not match
        the provided pattern.
        """
        if self._match_hint:
            hint = self._match_hint
        else:
            hint = self.default_match_hint
        
        signs = " ".join([f"<code>{sign}</code>" for sign in self.decimal_signs])

        hint = hint.replace("${min}", str(self.min))
        hint = hint.replace("${max}", str(self.max))
        hint = hint.replace("${decimal_signs}", signs)
        hint = hint.replace("${ndecimals}", str(self.ndecimals))

        return hint
    
    @property
    def default_match_hint(self) -> str:
        """
        str: Default match hint for this element, extracted from config.conf

        This property combines all match hints related to the 
        NumberEntry element and returns them as a single string.
        """
        name = f"{type(self).__name__}"

        c = self.experiment.config
        hints = []
        hints.append(c.get("hints", "match_" + name))

        if self.min is not None:
            hints.append(c.get("hints", "min_" + name))
        
        if self.max is not None:
            hints.append(c.get("hints", "max_" + name))
        
        hints.append(c.get("hints", "ndecimals_" + name))
        
        if self.ndecimals > 0 and self.decimal_signs is not None:
            hints.append(c.get("hints", "decimal_signs_" + name))
        
        return " ".join(hints)
    
    @property
    def input(self):
        """:meta private: (documented at :class:`.InputElement`)"""
        return self._input
    
    @input.setter
    def input(self, value: str):
        value = str(value)
        for sign in self.decimal_signs:
            value = value.replace(sign, ".")
        self._input = value

    def validate_data(self):
        """:meta private: (documented at :class:`.InputElement`)"""
        if not self.should_be_shown:
            return True
        
        if not self.force_input and self.input == "":
            return True
        
        elif not self.input:
            self.hint_manager.post_message(self.no_input_hint)
            return False
        
        try:
            in_number = float(self.input)
        except ValueError:
            self.hint_manager.post_message(self.match_hint)
            return False

        validate = True
        decimals = self.input.split(".")[-1] if "." in self.input else ""
        if self.min and in_number < self.min:
            self.hint_manager.post_message(self.match_hint)
            validate = False
        
        elif self.max and in_number > self.max:
            self.hint_manager.post_message(self.match_hint)
            validate = False
        
        elif len(decimals) > self.ndecimals:
            self.hint_manager.post_message(self.match_hint)
            validate = False
        return validate
        
    
    @property
    def codebook_data(self):
        """:meta private: (documented at :class:`.InputElement`)"""
        data = super().codebook_data

        data["ndecimals"] = self.ndecimals
        data["decimal_signs"] = " ".join(self.decimal_signs)
        data["min"] = self.min
        data["max"] = self.max

        return data

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
    disabled: bool = False


class ChoiceElement(InputElement, ABC):
    element_template = jinja_env.get_template("ChoiceElement.html.j2")
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
        d["type"] = self.type
        return d

    @abstractmethod
    def define_choices(self) -> list:
        pass


class SingleChoice(ChoiceElement):
    """"""

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
            choice.disabled = True if self.disabled else False

            if self.input:
                choice.checked = True if int(self.input) == i else False
            elif self.default is not None:
                choice.checked = True if self.default == i else False

            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)
        return choices

    @property
    def codebook_data(self):
        d = super().codebook_data

        for i, lab in enumerate(self.choice_labels, start=1):
            try:
                d.update({f"choice{i}": lab.text})  # if there is a text attribute, we use it.
            except AttributeError:
                d.update({f"choice{i}": str(lab)})  # otherwise __str__

        return d


class SingleChoiceButtons(SingleChoice):
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

    element_template = jinja_env.get_template("ChoiceButtons.html.j2")

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
            css = f"#{self.name} {{width: auto;}} "
            # and return to 100% with on small screens
            css += f"@media (max-width: 576px) {{#{self.name} {{width: 100%!important;}}}} "

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
            css = f"#{self.name} {{width: auto;}} "
            # and return to 100% with on small screens
            css += f"@media (max-width: 576px) {{#{self.name} {{width: 100%!important;}}}}"
            self._css_code += [(7, css)]

            # set width for each individual button
            for w, c in zip(self.button_width, self.choices):
                css = f"#{c.label_id} {{width: {w};}} "
                css += f"@media (max-width: 576px) {{#{c.label_id} {{width: 100%!important;}}}} "
                self._css_code += [(7, css)]

    def _round_corners(self):
        """Adds css for rounded buttons."""

        spec = "border-radius: 1rem;"
        css1 = f"div#{ self.name }.btn-group>label.btn.choice-button {{{spec}}}"
        css2 = f"div#{ self.name }.btn-group-vertical>label.btn.choice-button {{{spec}}}"
        self.add_css(css1)
        self.add_css(css2)

    def _toolbar(self):
        """Adds css for toolbar display instead of separate buttons."""

        not_ = "last", "first"
        margin = "right", "left"

        for exceptn, m in zip(not_, margin):
            n = "0" if m == "right" else "-1px"
            spec = f"margin-{m}: {n}; "
            spec += f"border-top-{m}-radius: 0; "
            spec += f"border-bottom-{m}-radius: 0;"
            css = (
                f"div#{ self.name }.btn-group>.btn.choice-button:not(:{exceptn}-child) {{{spec}}}"
            )
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
    button_group_class = "choice-button-bar"  # this leads to display as connected buttons
    button_toolbar = True
    button_round_corners = True


class MultipleChoice(ChoiceElement):
    """Checkboxes, allowing users to select multiple options.

    Defining 'min', 'max' implies force_input.
    """

    type = "checkbox"

    def __init__(
        self,
        *choice_labels,
        min: int = None,
        max: int = None,
        select_hint: str = None,
        default: Union[int, List[int]] = None,
        **kwargs,
    ):
        super().__init__(*choice_labels, **kwargs)

        self._input = {}

        if min is not None or max is not None:
            self.force_input = True

        self.min = min if min is not None else 0
        self.max = max if max is not None else len(self.choice_labels)
        self._select_hint = select_hint

        if isinstance(default, int):
            self.default = [default]
        elif default is not None and not isinstance(default, list):
            raise ValueError(
                "Default for MultipleChoice must be a list of integers, indicating the default choices."
            )
        else:
            self.default = default

    @property
    def select_hint(self):
        if self._select_hint:
            return self._select_hint
        else:
            hint = string.Template(self.experiment.config.get("hints", "select_MultipleChoice"))
            return hint.substitute(min=self.min, max=self.max)

    def validate_data(self):
        conditions = [True]

        if self.force_input and len(self.input) == 0:
            self.hint_manager.post_message(self.no_input_hint)
            conditions.append(False)

        if not (self.min <= sum(list(self.input.values())) <= self.max):
            self.hint_manager.post_message(self.select_hint)
            conditions.append(False)

        return all(conditions)

    @property
    def data(self):
        data = {}
        vals = [str(i) for i, (name, checked) in enumerate(self.input.items()) if checked]
        data["value"] = ",".join(vals)
        data.update(self.codebook_data)
        return {self.name: data}

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
            choice.value = i
            choice.id = f"{self.name}_choice{i}"
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


class MultipleChoiceButtons(MultipleChoice, SingleChoiceButtons):
    """Buttons, working as a MultipleChoice."""

    button_round_corners = False


class MultipleChoiceBar(MultipleChoiceButtons):
    """MultipleChoiceButtons, which are displayed as a toolbar instead
    of separate buttons.
    """

    button_group_class = "choice-button-bar"
    button_toolbar = True
    button_round_corners = False


class ButtonLabels(SingleChoiceButtons):
    """Disabled buttons. Example usecase might be additional labelling."""

    disabled = True

    @property
    def data(self):
        return {}


class BarLabels(SingleChoiceBar):
    """Disabled Button-Toolbar. Example usecase might be additional
    labelling.
    """

    disabled = True

    @property
    def data(self):
        return {}


class SubmittingButtons(SingleChoiceButtons):
    """SingleChoiceButtons that trigger submission of the current page
    on click.
    """

    def __init__(self, *choice_labels, button_style: Union[str, list] = "btn-info", **kwargs):
        super().__init__(*choice_labels, button_style=button_style, **kwargs)

    def added_to_page(self, page):
        super().added_to_page(page)

        t = jinja_env.get_template("submittingbuttons.js.j2")
        js = t.render(name=self.name)

        page += JavaScript(code=js)


class JumpButtons(SingleChoiceButtons):

    js_template = jinja_env.get_template("jumpbuttons.js.j2")

    def __init__(self, *choice_labels, button_style: Union[str, list] = "btn-primary", **kwargs):
        super().__init__(*choice_labels, button_style=button_style, **kwargs)
        self.choice_labels, self.targets = map(list, zip(*choice_labels))

    def prepare_web_widget(self):
        super().prepare_web_widget()

        self._js_code = []

        for choice, target in zip(self.choices, self.targets):
            js = self.js_template.render(id=choice.id, target=target)
            self.add_js(js)

    def validate_data(self):
        cond1 = bool(self.data) if self.force_input else True
        return cond1


class DynamicJumpButtons(JumpButtons):

    js_template = jinja_env.get_template("dynamic_jumpbuttons.js.j2")

    def validate_data(self):
        return True
        # cond1 = bool(self.data) if self.force_input else True

        # cond2 = True
        # for target in self.targets:
        #     value = self.experiment.data.get(target, None)
        #     cond2 = value in self.experiment.root_section.all_pages
        #     if not cond2:
        #         break

        # cond2 = all([target in self.experiment.root_section.all_pages for target in self.targets])
        # return cond1 and cond2


class SingleChoiceList(SingleChoice):
    element_template = jinja_env.get_template("SelectElement.html.j2")
    type = "select_one"

    def __init__(
        self, *choice_labels, toplab: str = None, size: int = None, default: int = 1, **kwargs
    ):
        super().__init__(*choice_labels, toplab=toplab, default=default, **kwargs)
        self.size = size

    @property
    def template_data(self):
        d = super().template_data
        d["size"] = self.size
        return d


class SelectPageList(SingleChoiceList):
    def __init__(
        self,
        toplab: str = None,
        scope: str = "exp",
        check_jumpto: bool = True,
        check_jumpfrom: bool = True,
        show_all_in_scope: bool = True,
        **kwargs,
    ):
        super().__init__(toplab=toplab, **kwargs)
        self.scope = scope
        self.check_jumpto = check_jumpto
        self.check_jumpfrom = check_jumpfrom
        self.show_all_in_scope = show_all_in_scope

    def _determine_scope(self) -> List[str]:

        if self.scope in ["experiment", "exp"]:
            scope = list(self.experiment.root_section.members["_content"].all_pages.values())
        elif self.scope == "section":
            scope = list(self.page.section.all_pages.values())
        else:
            try:
                target_section = self.experiment.root_section.all_members[self.scope]
                scope = list(target_section.all_pages.values())
            except AttributeError:
                raise AlfredError("Parameter 'scope' must be a section or page name.")

        choice_labels = []
        if not self.show_all_in_scope:
            for page in scope:
                jumpto_allowed = all([parent.allow_jumpto for parent in page.uptree()])
                if jumpto_allowed and page.should_be_shown:
                    choice_labels.append(page.name)
        else:
            choice_labels = [page.name for page in scope]

        return choice_labels

    def define_choices(self) -> List[Choice]:
        choices = []
        for i, page_name in enumerate(self.choice_labels, start=1):
            choice = Choice()

            choice.label = self._choice_label(page_name)
            choice.type = "radio"
            choice.value = page_name
            choice.name = self.name
            choice.id = f"choice{i}-{self.name}"
            choice.label_id = f"{choice.id}-lab"
            choice.disabled = True if self.disabled else self._jump_forbidden(page_name)
            choice.checked = self._determine_check(i)
            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)

        return choices

    def _jump_forbidden(self, page_name: str) -> bool:
        target_page = self.experiment.root_section.all_pages[page_name]

        forbidden = False

        # disable choice if the target page can't be jumped to
        if self.check_jumpto:
            forbidden = not (target_page.section.allow_jumpto)

        # disable choice if self can't be jumped from
        if self.check_jumpfrom:
            forbidden = not (self.page.section.allow_jumpfrom)

        # if not self.experiment.config.getboolean("general", "debug"):
        if not target_page.should_be_shown:
            forbidden = True

        return forbidden

    def _choice_label(self, page_name: str) -> str:
        target_page = self.experiment.root_section.all_pages[page_name]
        # shorten page title for nicer display
        page_title = target_page.title
        if len(page_title) > 35:
            page_title = page_title[:35] + "..."

        return f"{page_title} (name='{page_name}')"

    def _determine_check(self, i: int) -> bool:
        # set default value
        if self.default == i:
            checked = True
        elif int(self.input) == i:
            checked = True
        elif self.debug_enabled and i == 1:
            checked = True
        else:
            checked = False

        if self.experiment.config.getboolean("general", "debug"):
            current_page = self.experiment.movement_manager.current_page
            checked = i == (self.choice_labels.index(current_page.name) + 1)

        return checked

    def prepare_web_widget(self):
        self.choice_labels = self._determine_scope()
        self.choices = self.define_choices()

    def set_data(self, d):
        value = d.get(self.name)
        if value:
            self._input = self.choice_labels.index(value) + 1


class JumpList(Row):
    def __init__(
        self,
        scope: str = "exp",
        label: str = "Jump",
        check_jumpto: bool = True,
        check_jumpfrom: bool = True,
        debugmode: bool = False,
        show_all_in_scope: bool = True,
        button_style: Union[str, list] = "btn-dark",
        button_corners: str = "normal",
        **kwargs,
    ):

        random_name = "jumplist_" + uuid4().hex
        name = kwargs.get("name", random_name)
        select_name = name + "_select"
        btn_name = name + "_btn"
        select = SelectPageList(
            scope=scope,
            name=select_name,
            check_jumpto=check_jumpto,
            check_jumpfrom=check_jumpfrom,
            show_all_in_scope=show_all_in_scope,
        )
        btn = DynamicJumpButtons(
            (label, select_name),
            name=btn_name,
            button_style=button_style,
            button_corners=button_corners,
        )
        super().__init__(select, btn, **kwargs)

        self.layout.width_sm = [10, 2]
        self.debugmode = debugmode

    def prepare_web_widget(self):
        super().prepare_web_widget()
        if self.debugmode:
            for el in self.elements:
                el.disabled = False


# class ActionList(Element):

#     def __init__(self, list_element, button_element):
# self.list_element = list_element
# self.button_element = button_element


# class JumpList2(SelectPageList):
# def __init__(
#     self,
#     scope: str = "exp",
#     label: str = "Jump",
#     check_jumpto: bool = True,
#     check_jumpfrom: bool = True,
#     debugmode: bool = False,
#     show_all_in_scope: bool = True,
#     button_style: Union[str, list] = "btn-dark",
#     button_corners: str = "normal",
#     **kwargs,
# ):
#     name = kwargs.get("name", "jumplist_" + uuid4().hex)
#     select_name = name + "_select"
#     btn_name = name + "_btn"
#     self.btn = DynamicJumpButtons(
#         (label, select_name),
#         name=btn_name,
#         button_style=button_style,
#         button_corners=button_corners,
#     )
#     self.btn.should_be_shown = False
#     self.btn.add_css(f"#choice1-{self.btn.name}-lab {{border-top-left-radius: 0; border-bottom-left-radius: 0;}}")
#     super().__init__(
#         scope=scope,
#         name=select_name,
#         # suffix="test",
#         check_jumpto=check_jumpto,
#         check_jumpfrom=check_jumpfrom,
#         show_all_in_scope=show_all_in_scope,
#         )

# def _prepare_web_widget(self):
#     super()._prepare_web_widget()
#     self.btn._prepare_web_widget()
#     self.suffix = self.btn.inner_html

# def added_to_page(self, page):
#     super().added_to_page(page)
#     self.btn.added_to_page(page)

# def added_to_experiment(self, exp):
#     super().added_to_experiment(exp)
#     self.btn.added_to_experiment(exp)


class MultipleChoiceList(MultipleChoice):
    element_template = jinja_env.get_template("SelectElement.html.j2")
    type = "multiple"

    def __init__(self, *choice_labels, toplab: str = None, size: int = None, **kwargs):
        super().__init__(*choice_labels, toplab=toplab, **kwargs)
        self.size = size

    @property
    def template_data(self):
        d = super().template_data
        d["size"] = self.size
        return d

    def set_data(self, d):
        self._input = {}
        name_map = {str(choice.value): choice.name for choice in self.choices}
        val = d.get(self.name, None)
        val_name = name_map[val]

        for choice in self.choices:
            if choice.name == val_name:
                self._input[choice.name] = True
            else:
                self._input[choice.name] = False


class Image(Element):
    element_template = jinja_env.get_template("ImageElement.html.j2")

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
            url = self.experiment.ui.add_static_file(p)
            self.src = url
        else:
            self.src = self.url

    @property
    def template_data(self):
        d = super().template_data
        d["src"] = self.src
        return d


class Audio(Image):
    element_template = jinja_env.get_template("AudioElement.html.j2")

    def __init__(
        self,
        path: Union[str, Path] = None,
        url: str = None,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        align: str = "center",
        **kwargs,
    ):
        super().__init__(path=path, url=url, align=align, **kwargs)
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop

    @property
    def template_data(self):
        d = super().template_data
        d["controls"] = self.controls
        d["autoplay"] = self.autoplay
        d["loop"] = self.loop

        return d


class Video(Audio):
    """
    Displays a video on the page.

    .. note::

        You can specify a filepath or a url as the source, but not both
        at the same time.

    Args:
        path: Path to the video (relative to the experiment)
        url: Url to the video
        allow_fullscreen: Boolean, indicating whether users can enable
            fullscreen mode.
        video_height: Video height in absolute pixels (without unit).
            Defaults to "auto".
        video_width: Video width in absolute pixels (without unit).
            Defaults to "100%". It is recommended to use leave this
            parameter at the default value and use the general element
            parameter *width* for setting the width.

        **kwargs: The following keyword arguments are inherited from
            :class:`.Audio`:

            * controls
            * autoplay
            * loop

    """

    element_template = jinja_env.get_template("VideoElement.html.j2")

    def __init__(
        self,
        path: Union[str, Path] = None,
        url: str = None,
        allow_fullscreen: bool = True,
        video_height: str = "auto",
        video_width: str = "100%",
        **kwargs,
    ):
        super().__init__(path=path, url=url, **kwargs)
        self.video_height = video_height
        self.video_width = video_width
        self.allow_fullscreen = allow_fullscreen

    @property
    def template_data(self):
        d = super().template_data
        d["video_height"] = self.video_height
        d["video_width"] = self.video_width
        d["allow_fullscreen"] = self.allow_fullscreen

        return d


class MatPlot(Element):
    """
    Displays a :class:`matplotlib.figure.Figure` object.

    .. note::
        When plotting in alfred, you need to use the Object-oriented
        matplotlib API
        (https://matplotlib.org/3.3.3/api/index.html#the-object-oriented-api).

    Args:
        fig (matplotlib.figure.Figure): The figure to display.
        align: Alignment of the figure ('left', 'right', or 'center').
            Defaults to 'center'.

    Examples:

        Example usage is illustrated here. Note that the ``example_plot```
        will only be displayed if it is added to a page.

        >>> import alfred3 as al
        >>> from matplotlib.figure import Figure

        >>> fig = Figure()
        >>> ax = fig.add_subplot()
        >>> ax.plot(range(10))
        >>> example_plot = al.MatPlot(fig=fig, name="example))
        >>> example_plot
        MatPlot(name="example")

    """

    element_template = jinja_env.get_template("ImageElement.html.j2")

    def __init__(self, fig, align: str = "center", **kwargs):
        super().__init__(align=align, **kwargs)
        self.fig = fig
        self.src = None

    def prepare_web_widget(self):
        out = io.BytesIO()
        self.fig.savefig(out, format="svg")
        out.seek(0)
        self.src = self.exp.ui.add_dynamic_file(out, content_type="image/svg+xml")

    @property
    def template_data(self):
        d = super().template_data
        d["src"] = self.src
        return d
