"""
Provides fundamental element classes.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>

"""

from abc import ABC, abstractproperty, abstractmethod
from typing import List
from typing import Tuple
from typing import Union
from typing import Iterator
from dataclasses import dataclass

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import Template

from .. import alfredlog
from ..messages import MessageManager
from ..exceptions import AlfredError
from .._helper import fontsize_converter
from .._helper import check_name
from .._helper import inherit_kwargs


#: jinja Environment giving access to included jinja-templates.
jinja_env = Environment(loader=PackageLoader(__name__, "templates"))


class Element:
    """
    Element baseclass, providing basic functionality for all elements.

    Args:
        name: Name of the element. This should be a unique identifier.
            It will be used to identify the corresponding data in the
            final data set.
        font_size: Font size for text in the element. You can use a 
            keyword or an exact specification. The available keywords 
            are 'tiny', 'small', 'normal', 'big', and 'huge'. The exact
            specification shoul ideally include a unit, such as '1rem',
            or '12pt'. If you supply an integer without a unit, a unit
            of 'pt' will be assumed. Defaults to 'normal'.
        align: Horizontal alignment of text in the element. Does not
            usually apply to labels. Think of it as an alignment that
            applies to the innermost layer of an element (while labels
            are generally located at outer layers). See
            :class:`.LabelledElement` for more on labelled elements.
            Can be 'left' (default), 'center', 'right', or 'justify'.
        position: Horizontal position of the full element on the
            page. Values can be 'left', 'center' (default), 'end',
            or any valid value for the justify-content
            `flexbox utility <https://getbootstrap.com/docs/4.0/utilities/flex/#justify-content>`_.
            Takes effect only, when the element is not
            full-width.
        width: Defines the horizontal width of the element from
            small screens upwards. It is always full-width on extra
            small screens. Possible values are 'narrow', 'medium',
            'wide', and 'full'. For more detailed control, you can
            define the :attr:`.element_width` attribute.
        height: Vertical height of the elements display area. Supply a
            string with a unit, e.g. "80px". Usually, the default is
            fine. For adding vertical space to a page, you should prefer
            the :class:`.VerticalSpace` element, as it is sematically
            more clear.
        showif: A dictionary, defining conditions that must be met
            for the element to be shown. The conditions take the form of
            key-value pairs, where each key is an element name and the
            value is the required input. See :attr:`showif` for details.
        instance_log: If *True*, the element will use an
            instance-specific logger, thereby allowing detailed fine-
            tuning of its logging behavior.

    See Also:
        * How to create a custom element

    Notes:
        The Element does not have its own display. It is used only
        to inherit functionality.


    """

    #: Base template for the element, which will be used to hold the
    #: rendered element template. Gets rendered by :attr:`.Element.web_widget`
    base_template: Template = jinja_env.get_template("html/Element.html.j2")

    #: The element's specific, inner template. Gets rendered by
    #: :meth:`.render_inner_html`
    element_template: Template = None

    _inherited_kwargs = {}

    def __init__(
        self,
        name: str = None,
        font_size: Union[str, int] = None,
        align: str = "left",
        width: str = "full",
        height: str = None,
        position: str = "center",
        showif: dict = None,
        instance_log: bool = False,
    ):

        self.name: str = name  # documented in getter property
        self.page = None  # documented in getter
        self.exp = None  # documented in getter
        self.experiment = None  # documented in getter

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

        self.display_standalone = True

        # additional code
        self._css_code = []  # documented in getter property
        self._css_urls = []  # documented in getter property
        self._js_code = []  # documented in getter property
        self._js_urls = []  # documented in getter property

        #: Boolean flag, indicating whether the element should spawn
        #: its own logger, or use the class-specific logger.
        #: Can be set to *True* to allow for very fine-grained logging.
        #: In most cases, it is fine to leave it at the default (*False*)
        self.instance_log: bool = instance_log

        #: A :class:`~.QueuedLoggingInterface`, offering logging
        #: through the methods *debug*, *info*, *warning*, *error*,
        #: *exception*, and *log*.
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)

        if position != "center" and width == "full":
            self.log.warning(
                (
                    "You have changed the value of 'position' on a full-width element. "
                    "That will most likely not have an effect. Did you mean to change 'align'?"
                )
            )

    @property
    def page(self):
        """
        alfred3.Page: The page to which this element belongs.
        """
        return self._page

    @page.setter
    def page(self, page):
        self._page = page

    @property
    def exp(self):
        """
        alfred3.ExperimentSession: The experiment session to which this
        element belongs.
        """
        return self._exp

    @exp.setter
    def exp(self, exp):
        self._exp = exp

    @property
    def experiment(self):
        """
        Alias for :attr:`.exp`
        """
        return self._exp

    @experiment.setter
    def experiment(self, exp):
        self.exp = exp

    @property
    def display_standalone(self):
        """
        bool: If *True* (default), the element will be displayed as 
        usual on its own. If *False*, the element will not be displayed
        unless you incorporate its :attr:`.Element.web_widget` in some
        other way.

        Notes:
            An element with ``display_standalone = False`` will still be validated.

        See Also:
            Similar to :attr:`.Element.should_be_shown`. The main 
            difference is that an element with 
            ``display_standalone = False`` will still be validated, while an
            element with ``should_be_shown = False`` will never be 
            validated.
        """
        return self._display_standalone
    
    @display_standalone.setter
    def display_standalone(self, value):
        self._display_standalone = value

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

                    def on_exp_access(self):
                        self += al.Text("This is text", showif={"exp_condition": "one"})

            This is a more complex condition using the hook method. The
            text element on *page2* will only be show to subjects, if
            they spent more than 20 seconds on *page1*::

                import alfred3 as al
                exp = al.Experiment()
                exp += al.Page(name="FirstPage")

                @exp.member
                class SecondPage(al.Page):

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

        .. _Bootstrap 4's 12-column-grid system: https://getbootstrap.com/docs/4.0/layout/grid/

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

        This version of the tree omits the ``_root`` part.
        """

        return self.tree.replace("_root.", "")

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
            passed to :attr:`.element_template` and :attr:`.base_template`.

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
        d["fontsize"] = f"font-size: {self.font_size};" if self.font_size is not None else ""
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

            t = jinja_env.get_template("js/showif.js.j2")
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
        from .. import page as pg

        if not isinstance(page, pg._PageCore):
            raise TypeError()

        self.page = page
        if self.name is None:
            self.name = self.page._generate_element_name(self)

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
        return f"{type(self).__name__}(name='{self.name}')"

    def __repr__(self):
        return self.__str__()

    # abstract attributes start here -----------------------------------

    @property
    def _inner_html(self) -> str:
        """
        Shortcut for rendering the element template on its own with
        the template data.

        Notes:
            This should not be used together with :attr:`.web_widget`,
            because it will lead to :attr:`.template_data` being called
            twice. Calling the template data twice will empty all
            corrective hints, causing them to not be displayed at all.

        """
        return self.render_inner_html(self.template_data)

    def render_inner_html(self, template_data: dict) -> str:
        """
        Renders the element template :attr:`~.element_template`.

        Args:
            template_data: A dictionary of data for rendering the
                template.

        Notes:
            If no `element_template` is defined, `None` is returned. Usually,
            the inner html gets placed into the higher-level
            :attr: `.base_template`, when :attr:`Element.web_widget` gets called.

        Returns:
            str: Inner html code for this element.
        """
        if self.element_template is not None:
            return self.element_template.render(template_data)
        else:
            return None

    @property
    def web_widget(self) -> str:
        """
        The element's rendered html code for display on a page.

        Notes:
            This function gets the :attr:`.template_data`, and uses it
            to first call :meth:`.render_inner_html`, and then render
            the :attr:`.base_template`.

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


class RowLayout:
    """
    Provides layouting functionality for responsive horizontal
    positioning of elements.

    Default behavior is to have equal-width columns with an automatic
    breakpoint on extra small screens (i.e. all columns get the bootstrap
    class 'col-sm' by default).

    The layout's width attributes can be accessed and changed to customize
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
        self.ncols: int = ncols
        self._valign_cols = valign_cols if valign_cols is not None else []
        self.responsive: bool = responsive  # documented in getter

        self._width_xs: List[int] = None  # documented in getter
        self._width_sm: List[int] = None  # documented in getter
        self._width_md: List[int] = None  # documented in getter
        self._width_lg: List[int] = None  # documented in getter
        self._width_xl: List[int] = None  # documented in getter

    @property
    def ncols(self):
        """
        int: Number of columns
        """
        return self._ncols

    @ncols.setter
    def ncols(self, value):
        self._ncols = value

    @property
    def responsive(self):
        """
        bool: Indicates whether breakpoints should be responsive, or not.
        """
        return self._responsive

    @responsive.setter
    def responsive(self, value):
        self._responsive = value

    @property
    def width_xs(self):
        """
        List[int]: List of column widths on screens of size 'xs' or bigger
        (<576px). Content must be integers between 1 and 12.
        """
        return self._width_xs

    @width_xs.setter
    def width_xs(self, value):
        try:
            assert isinstance(value[0], int)
        except (AssertionError, TypeError):
            raise ValueError("width must be a list of integers")
        
        try:
            assert len(value) <= self.ncols
        except AssertionError:
            raise ValueError(f"Number of widths must be smaller or equal to the number of columns ({self.ncols}), not {len(value)}.")

        self._width_xs = value

    @property
    def width_sm(self):
        """
        List[int]: List of column widths on screens of size 'sm' or bigger
        (>=576px). Content must be integers between 1 and 12.
        """
        return self._width_sm

    @width_sm.setter
    def width_sm(self, value):
        try:
            assert isinstance(value[0], int)
        except AssertionError:
            raise ValueError("width must be a list of integers")

        try:
            assert len(value) <= self.ncols
        except AssertionError:
            raise ValueError(f"Number of widths must be smaller or equal to the number of columns ({self.ncols}), not {len(value)}.")

        self._width_sm = value

    @property
    def width_md(self):
        """
        List[int]: List of column widths on screens of size 'md' or bigger
        (>=768px). Content must be integers between 1 and 12.
        """
        return self._width_md

    @width_md.setter
    def width_md(self, value):
        try:
            assert isinstance(value[0], int)
        except AssertionError:
            raise ValueError("width must be a list of integers")
        
        try:
            assert len(value) <= self.ncols
        except AssertionError:
            raise ValueError(f"Number of widths must be smaller or equal to the number of columns ({self.ncols}), not {len(value)}.")

        self._width_md = value

    @property
    def width_lg(self):
        """
        List[int]: List of column widths on screens of size 'lg' or bigger
        (>=992px). Content must be integers between 1 and 12.
        """
        return self._width_lg

    @width_lg.setter
    def width_lg(self, value):
        try:
            assert isinstance(value[0], int)
        except AssertionError:
            raise ValueError("width must be a list of integers")
        
        try:
            assert len(value) <= self.ncols
        except AssertionError:
            raise ValueError(f"Number of widths must be smaller or equal to the number of columns ({self.ncols}), not {len(value)}.")

        self._width_lg = value

    @property
    def width_xl(self):
        """
        List[int]: List of column widths on screens of size 'xl' or bigger
        (>=1200px). Content must be integers between 1 and 12.
        """
        return self._width_xl

    @width_xl.setter
    def width_xl(self, value):
        try:
            assert isinstance(value[0], int)
        except AssertionError:
            raise ValueError("width must be a list of integers")
        
        try:
            assert len(value) <= self.ncols
        except AssertionError:
            raise ValueError(f"Number of widths must be smaller or equal to the number of columns ({self.ncols}), not {len(value)}.")

        self._width_xl = value

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


@inherit_kwargs
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

        {kwargs}

    Notes:

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

            |======================|=====================|
            |   el1                |  el2                |
            |======================|=====================|

        An example with customized widths, where we redefine the
        "sm" breakpoint::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    el1 = al.Text("text")
                    el2 = al.TextEntry(toplab="lab", name="example")

                    row = al.Row(el1, el2)
                    row.layout.width_sm = [2, 10]

                    self += row

        The arrangement will look like this::

            |===========|===============================|
            |   el1     |  el2                          |
            |===========|===============================|


    """

    element_template = jinja_env.get_template("html/Row.html.j2")

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

        self.elements: list = elements  # documented in getter
        self.layout = RowLayout(
            ncols=len(self.elements), valign_cols=valign_cols
        )  # documented in getter
        self.elements_full_width: bool = elements_full_width  # documented in getter

    @property
    def elements(self):
        """
        List[Element]: List of the elements in this row.
        """
        return self._elements

    @elements.setter
    def elements(self, value):
        self._elements = value

    @property
    def layout(self):
        """
        RowLayout: The layout of this row, can be used to finetune
        column widths via its attributes. See :class:`.RowLayout` for
        the available width attributes.
        """
        return self._layout

    @layout.setter
    def layout(self, value):
        self._layout = value

    @property
    def elements_full_width(self):
        """
        bool: If *True*, all elements will take up the full horizontal
        space of their column, regardless of the element's
        :attr:`.Element.element_width` and :attr:`.Element.width`
        attributes.

        This is done by default for better default layouting.
        """
        return self._elements_full_width

    @elements_full_width.setter
    def elements_full_width(self, value):
        self._elements_full_width = value

    def added_to_page(self, page):

        super().added_to_page(page)

        for element in self.elements:
            if element is None:
                continue
            element.display_standalone = False
            page += element

            if self.elements_full_width:
                element.width = "full"

    def _prepare_web_widget(self):

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

        d = super().template_data
        d["columns"] = self._cols
        d["name"] = self.name
        return d


@inherit_kwargs
class Stack(Row):
    """
    Stacks multiple elements on top of each other.

    Stacks are intended for use in Rows. They allow you to flexibly
    arrange elements in a grid.

    Args:
        *elements: The elements to stack.

        {kwargs}

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

                    stack = al.Stack(el1, el2)
                    self += al.Row(stack, el3)

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


@inherit_kwargs
class LabelledElement(Element):
    """
    An intermediate Element class which provides support for labels.

    This class is used as a base class for all elements that come
    equipped with labels.

    Args:
        toplab, bottomlab, leftlab, rightlab: Labels above, below, left
            and right of the element.

        layout: Can be one of the following: 1) An instance of
            :class:`.RowLayout`, or 2) a tuple of integers, specifying 
            the allocation of horizontal space between leftlab, main 
            element widget and rightlab on small screens upwards. 

            Option 1) offers fine-tuned flexibility, 2) uses a default
            RowLayout and changes the :attr:`.RowLayout.width_sm` 
            attribute.

            By default, the layout is set automatically depending on the
            specification of the left and right labels.


        {kwargs}

    Notes:
        The labelled element is not supposed to be included on a page on
        its own - it is meant for easy derivation of new elements.

    """

    base_template = jinja_env.get_template("html/LabelledElement.html.j2")

    def __init__(
        self,
        toplab: str = None,
        leftlab: str = None,
        rightlab: str = None,
        bottomlab: str = None,
        layout: Union[RowLayout, Tuple[int]] = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(**kwargs)

        self._ncols = len([x for x in [leftlab, rightlab, 1] if x is not None])
        self._input_col = 1 if leftlab is not None else 0

        if isinstance(layout, RowLayout):
            self.layout = layout
        else:
            self.layout = RowLayout(ncols=self._ncols)
            self.layout.valign_cols = ["center"]

            if leftlab and rightlab:
                width_sm = layout if layout is not None else [2, 8, 2]
            elif leftlab:
                width_sm = layout if layout is not None else [3, 9]
            elif rightlab:
                width_sm = layout if layout is not None else [9, 3]
            else:
                width_sm = [12]

            self.layout.width_sm = width_sm

        self.toplab = toplab
        self.leftlab = leftlab
        self.rightlab = rightlab
        self.bottomlab = bottomlab

    @property
    def layout(self):
        """
        RowLayout: Controls the allocation of horizontal space between
        the left and right label, as well as the main element.
        """
        return self._layout

    @layout.setter
    def layout(self, value: RowLayout):
        try:
            if not value.ncols == self._ncols:
                raise AlfredError(
                    (
                        "The number of layout columns must match the specification of "
                        f"left and right labels. In this case, you need {self._ncols} columns."
                    )
                )
            self._layout = value
        except AttributeError:
            raise TypeError("Layout must be an instance of 'alfred3.RowLayout'.")


    def added_to_page(self, page):

        super().added_to_page(page)

        for lab in ["toplab", "leftlab", "rightlab", "bottomlab"]:
            if getattr(self, lab):
                getattr(self, lab).name = f"{self.name}_{lab}"

    def added_to_experiment(self, experiment):

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
        from .display import Label

        if isinstance(value, Label):
            self._toplab = value
        elif isinstance(value, str):
            self._toplab = Label(text=value, align="center", name=f"{self.name}_toplab")
        else:
            self._toplab = None

    @property
    def bottomlab(self):
        """.Label: Label below of the main element widget."""
        return self._bottomlab

    @bottomlab.setter
    def bottomlab(self, value: str):
        from .display import Label

        if isinstance(value, Label):
            self._bottomlab = value
        elif isinstance(value, str):
            self._bottomlab = Label(text=value, align="center", name=f"{self.name}_bottomlab")
        else:
            self._bottomlab = None

    @property
    def leftlab(self):
        """.Label: Label to the left of the main element widget."""
        return self._leftlab

    @leftlab.setter
    def leftlab(self, value: str):
        from .display import Label

        if isinstance(value, Label):
            self._leftlab = value
            self._leftlab.layout = self._layout
            self._leftlab.layout_col = 0
        elif isinstance(value, str):
            self._leftlab = Label(text=value, align="right", name=f"{self.name}_leftlab")
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
        from .display import Label

        if isinstance(value, Label):
            self._rightlab = value
            self._rightlab.layout = self._layout
            self._rightlab.layout_col = self._input_col + 1
        elif isinstance(value, str):
            self._rightlab = Label(text=value, align="left", name=f"{self.name}_rightlab")
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

        d = super().template_data
        d["toplab"] = self.toplab
        d["leftlab"] = self.leftlab
        d["rightlab"] = self.rightlab
        d["bottomlab"] = self.bottomlab
        d["input_breaks"] = self.layout.col_breaks(col=self._input_col)
        d["input_valign"] = self.layout.valign_cols[self._input_col]
        return d


@inherit_kwargs
class InputElement(LabelledElement):
    """
    Base class for elements that allow data input.

    Args:
        force_input: If `True`, users can  only progress to the next page
            if they enter data into this field. Note that a
            :class:`.NoValidationSection` or similar sections might
            overrule this setting.

            A general, experiment-wide setting for force_input can be
            placed in the config.conf (section "general"). That setting
            is used by default and can be overruled here for individual
            elements. Defaults to False.

            The experiment-wide default can be changed in config.conf.

        default: Default value. Type depends on the element type.
        prefix: Prefix for the input field.
        suffix: Suffix for the input field.
        description: An additional description of the element. This will
            show up in the alfred-generated codebook. It has
            no effect on the display of the experiment, as it only
            serves as a descriptor for humans.
        no_input_hint: Hint to be displayed if
            *force_input* set to True and no user input registered.
            Defaults to the experiment-wide default value
            specified in config.conf.

        {kwargs}

    Notes:
        The InputElement does not have its own display. It is used only
        to inherit functionality.

    """

    def __init__(
        self,
        toplab: str = None,
        force_input: bool = None,
        default: Union[str, int, float] = None,
        prefix: Union[str, Element] = None,
        suffix: Union[str, Element] = None,
        description: str = None,
        disabled: bool = False,
        no_input_hint: str = None,
        **kwargs,
    ):
        super().__init__(toplab=toplab, **kwargs)

        self.description = description  # documented in getter
        self.input = ""  # documented in getter
        self._force_input = force_input  # documented in getter property
        self._no_input_hint = no_input_hint
        self._default = default  # documented in getter property
        self._prefix = prefix  # documented in getter property
        self._suffix = suffix  # documented in getter property
        self.show_hints: bool = True
        self._hint_manager = MessageManager(default_level="danger")  # documented in getter
        self.disabled: bool = disabled  # documented in getter

        if default is not None:
            self.input = default

        if self._force_input and (self._showif_on_current_page or self.showif):
            raise ValueError(f"Elements with 'showif's can't be 'force_input' ({self}).")

    @property
    def show_hints(self):
        """
        bool: Flag, indicating whether corrective hints regarding
        this element should be shown.
        """
        return self._show_hints

    @show_hints.setter
    def show_hints(self, value):
        self._show_hints = value

    @property
    def description(self):
        """
        str: Detailed description of this element to be added to the
        automatically generated codebook
        """
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def disabled(self):
        """
        bool: A boolean flag, indicating whether the element is disabled
        A disabled input element is shown and displays its input
        value, but subjects cannot enter any data.
        """
        return self._disabled

    @disabled.setter
    def disabled(self, value):
        self._disabled = value

    @property
    def hint_manager(self):
        """
        MessageManager: A :class:`.MessageManager`, handling the corrective hints
        for this element.
        """
        return self._hint_manager

    def _prepare_web_widget(self):

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

        d = super().template_data
        d["default"] = self.default
        d["prefix"] = self.prefix
        d["suffix"] = self.suffix
        d["input"] = self.input
        d["disabled"] = self.disabled
        if self.show_hints:
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
        if not self.should_be_shown:
            return True

        elif self.force_input and not self.input:
            self.hint_manager.post_message(self.no_input_hint)
            return False

        else:
            return True

    @property
    def no_input_hint(self) -> str:
        """
        str: Hint for subjects, if they left a *force_input* field empty.
        """
        if self._no_input_hint:
            return self._no_input_hint
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

        If the prefix is an element, the getter returns only its
        inner html. If it is a string, the getter
        returns the text, wrapped in an appropriate html container.
        """
        try:
            return self._prefix._inner_html
        except AttributeError:
            return self._render_input_group_text(self._prefix)

    @property
    def suffix(self):
        """
        Union[str, Element]: A string or element, serving as suffix.

        If the suffix is an element, the getter returns only its
        inner html. If it is a string, the getter
        returns the text, wrapped in an appropriate html container.
        """
        try:
            return self._suffix._inner_html
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
        data["prefix"] = self.prefix
        data["suffix"] = self.suffix
        data["default"] = self.default
        data["description"] = self.description
        data["unlinked"] = True if isinstance(self.page, page.UnlinkedDataPage) else False
        return data

    def added_to_page(self, page):

        from .. import page as pg

        if not isinstance(page, pg._PageCore):
            raise TypeError()

        self.page = page
        if self.name is None:
            raise ValueError(f"{self} is not named. Input elements must be named")

        if page.prefix_element_names:
            self.name = f"{self.page.name}_{self.name}"

        if self.page.experiment and not self.experiment:
            self.added_to_experiment(self.page.experiment)
        elif self.experiment:
            if self.name in self.experiment.root_section.all_updated_elements:
                raise AlfredError(
                    f"Element name '{self.name}' is already present in the experiment."
                )

        for fix in (self._prefix, self._suffix):
            try:
                fix.should_be_shown = False
                self.page += fix
            except AttributeError as e:
                self.log.debug(f"Exception passed silently: {e}")
                pass


@dataclass
class _Choice:
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


@inherit_kwargs(from_=[InputElement])
class ChoiceElement(InputElement, ABC):
    """
    Baseclass for derivation of choice elements.

    Args:
        *choice_labels: Variable number of strings or suitable elements
            to be used as choice labels. The number of labels determines
            the number of choices. We don't enforce harsh restrictions
            on the types of elements that can be used as choice labels,
            so it is up to you to make sensible choices. A common case
            would be an :class:`.Image`.
        vertical: Boolean switch, indicating whether the choices should
            be listed vertically. Defaults to *False*, i.e. horizontal
            display.

        {kwargs}

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/ChoiceElement.html.j2")

    #: Choice type (e.g. "radio" for radio inputs and "checkbox")
    #: for multiple choice inputs
    type: str = None

    #: Switch for turning the interpretation of emoji shortcodes in the
    #: choice labels off, if necessary. Defaults to *True*.
    emojize: bool = True

    def __init__(
        self,
        *choice_labels: Union[str, Element],
        vertical: bool = False,
        align: str = "center",
        **kwargs,
    ):
        super().__init__(align=align, **kwargs)

        self._input = {}

        self.choice_labels = choice_labels  # documented in getter
        self.vertical = vertical  # documented in getter

        #: List of choices that belong to this element.
        self.choices: List[_Choice] = None

    @property
    def vertical(self):
        """
        bool: Attribute defining, whether the element is displayed vertically.
        """
        return self._vertical

    @vertical.setter
    def vertical(self, value):
        self._vertical = value

    @property
    def choice_labels(self):
        """
        list: Stored list of choice labels.
        """
        return self._choice_labels

    @choice_labels.setter
    def choice_labels(self, value: list):
        self._choice_labels = value

    def added_to_page(self, page):
        """
        If choice labels are element instances, they are added to the
        page to enable their full functionality.

        :meta private: (documented at :class:`.InputElement`)
        """
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
    def define_choices(self) -> List[_Choice]:
        """
        Abstract method for the definition of the individual choices
        belonging to this element.

        Must be redefined by inheriting elements and return a list
        of :class:`.Choice` instances.
        """
        pass

    @property
    def codebook_data(self):

        d = super().codebook_data

        for i, lab in enumerate(self.choice_labels, start=1):
            try:
                d.update({f"choice{i}": lab.text})  # if there is a text attribute, we use it.
            except AttributeError:
                d.update({f"choice{i}": str(lab)})  # otherwise __str__

        return d

    @property
    def input(self) -> dict:
        """
        Dict[str, bool]: Dictionary of subject inputs.

        Contains the choice labels as keys and their selection status
        (*True* for selected choices, *False* otherwise) as values.
        """
        return self._input

    @input.setter
    def input(self, value):
        self._input = value