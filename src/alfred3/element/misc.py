"""
Provides elements that don't fit into the other categories.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""
import time

from pathlib import Path
from typing import Union

from jinja2 import Template

from .core import Element
from .core import InputElement
from .core import jinja_env


class Style(Element):
    """
    Adds CSS code to a page.

    CSS styling can be used to change the appearance of page or
    individual elements.

    Args:
        code: CSS code.
        url: Url to CSS code.
        path: Path to a .css file.
        priority: Controls the order in which CSS files are placed on a
            page. Lower numbers are included first. Can be useful, if
            you have trouble with overriding rules. In everyday use, 
            it's fine to stick with the default.

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

    Examples:
        Minimal example, turning the color of a specific text element 
        red. The element is selected by its id::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Text("Element 1", name="test_el")
                    self += al.Style(code="#test_el {color: red;}")

        Minimal example, turning the color of all text elements on a
        specific page red. The elements are selected by their class::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Style(code=".Text-element {color: red;}")

                    self += al.Text("Element 1", name="test_el1")
                    self += al.Text("Element 2", name="test_el2")


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
            raise ValueError(
                "You can only specify one of 'code', 'url', or 'path'.")

    @property
    def css_code(self):
        if not self.code:
            return []

        if self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def css_urls(self):

        if self.url:
            return [(self.priority, self.url)]
        else:
            return []


class HideNavigation(Style):
    """
    Removes the forward/backward/finish navigation buttons from a page.

    See Also:

        * With :class:`.NoNavigationPage`, you can achieve the same 
          result. As a rule of thump, use the HideNavigation element,
          if you want to affect the display of navigation elements
          dynamically, and the NoNavigationPage, if the page in question
          will always be displayed with navigation elements.

        * Using :class:`.JumpButtons` and :class:`.JumpList`, you can add
          custom navigation elements to a page.

        * By defining the :meth:`.Page.custom_move` method on a page,
          you can implement highly customized movement behavior.

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.HideNavigation()

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

    Args:
        code: Javascript code.
        url: Url to Javascript code.
        path: Path to a .js file.
        priority: Controls the order in which Javascript code is placed 
            on a page. Lower numbers are included first. Can be useful, 
            if you have trouble with overriding code. In everyday use, 
            it's fine to stick with the default.

    Notes:
        You can use the jquery API (version 3.5.1 as of 2021-01-20).

    See Also:
        * See :attr:`.Element.css_class_element` and
          :attr:`.Element.css_class_container` for information on
          element CSS classes and IDs.
        * The method :meth:`.Element.add_js` can be used to add JS
          to a specific element.

    Examples:

            In this example, we use JavaScript to create a text element
            that will lead to automatic submission of the current page,
            when a change to its input is detected::

                import alfred3 as al
                exp = al.Experiment()

                @exp.member
                class HelloWorld(al.Page):
                    name = "hello_world"

                    def on_exp_access(self):

                        js_code = '''
                        $( '#test_el' ).on('change', function() {
                            $( '#form' ).submit();
                        };)
                        '''

                        self += al.JavaScript(code=js_code)
                        self += al.Text("Element 1", name="test_el")

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
            raise ValueError(
                "You can only specify one of 'code', 'url', or 'path'.")

    @property
    def js_code(self):
        if not self.code and not self.path:
            return []

        elif self.path:
            p = self.experiment.subpath(self.path)

            code = p.read_text()
            return [(self.priority, code)]
        else:
            return [(self.priority, self.code)]

    @property
    def js_urls(self):

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

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.WebExitEnabler()


    """

    def __init__(self):
        """Constructor method"""
        super().__init__(code="allow_leaving();", priority=10)


class Value(InputElement):
    """
    Value elements can be used to save data without any display.

    Args:
        value: The value that you want to save.
        name: Name of the element. This should be a unique identifier.
            It will be used to identify the corresponding data in the
            final data set.

    Examples:

        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    self += al.Value("test", name="myvalue")

    """

    def __init__(self, value: Union[str, int, float], name: str):
        """Constructor method."""
        super().__init__(name=name)

        #: The value that you want to save.
        self.input: Union[str, int, float] = value
        self.should_be_shown = False


class Data(Value):
    """Alias for :class:`.Value`."""
    pass


class Callback(Element):
    """
    Triggers execution of a python function from a loaded page.

    Args:
        func (callable): Python function to be called on button click.
            The function must take zero arguments, but it can be a 
            method of a class or instance.

        followup (str): What to do after the python function was called.
            Can take the following values: 

            - ``refresh`` submits and reloads the current page (default),
            - ``none`` does nothing,
            - ``forward`` submits the current page and moves forward,
            - ``backward`` submits the current page and moves backward,
            - ``jump>page_name`` submits the current page and triggers
              a jump to a page with the name 'page_name'
            - ``custom`` executes custom JavaScript. If you choose this 
              option, you must supply your custom JavaScript through the
              argument *custom_js*.

        submit_first (bool): If True, the current values of all input
            elements on the current page will be saved on button click,
            before *func* is called. This way, these values will be
            available in *func* through :attr:`.ExperimentSession.values`, 
            if func has access to the ExperimentSession object.
            See Example 3. Defaults to True.

        delay (int): Number of seconds to wait before the callback is
            triggered. Defaults to 0.

        reset_delay (bool): If *True*, the delay will start from the 
            beginning every time the page is reloaded, refreshed, or
            revisited. Defaults to *False*.

        custom_js (str): Custom JavaScript to execute after the python
            function specified in *func* was called. Only takes effect,
            if *followup* is set to 'custom'.

    Examples:
        
        The callback on the first page will trigger after a delay of 10 
        seconds. It will print the experiment id to the terminal::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):

                def on_exp_access(self):
                    self += al.Callback(func=self.print_expid, delay=10)

                def print_expid(self):
                    print(self.exp.exp_id)
    """

    web_widget = None
    should_be_shown = False

    #: Javascript template
    js_template = jinja_env.get_template("js/callback.js.j2")

    def __init__(self, func: callable, followup: str = "refresh", submit_first: bool = True, delay: int = 0, reset_delay: bool = False, custom_js: str = ""):
        super().__init__()
        self.func = func
        self.followup = followup
        self.url = None
        self.delay_original = delay
        self.delay = None
        self.start_time = None
        self.reset_delay = reset_delay
        self.submit_first = submit_first
        self.custom_js = custom_js

    @property
    def followup(self) -> str:
        """
        str: Value of the 'followup' setting for this element.
        """
        return self._followup

    @followup.setter
    def followup(self, value):
        if value not in {"refresh", "forward", "backward", "none", "custom"} and not value.startswith("jump>"):
            raise ValueError(f"Invalid value for 'followup': {value}")
        self._followup = value

    def prepare_web_widget(self):
        # docstring inherited
        self._js_code = []
        super().prepare_web_widget()
        self.url = self.exp.ui.add_callable(self.func)

        if self.delay_original == 0:
            self.delay = self.delay_original
        elif not self.start_time:
            self.start_time = time.time()
            self.delay = self.delay_original
        elif not self.reset_delay:
            now = time.time()
            already_passed = now - self.start_time
            self.delay = self.delay_original - already_passed

        d = {}
        d["url"] = self.url
        d["followup"] = self.followup
        d["timeout"] = self.delay
        d["submit_first"] = self.submit_first
        d["custom_js"] = self.custom_js
        d["set_data_url"] = self.exp.ui.set_page_data_url

        js = self.js_template.render(d)

        self.add_js(js)


class RepeatedCallback(Element):
    """
    Triggers repeated execution of a python function from a loaded page.

    Args:
        func (callable): Python function to be called on button click.
            The function must take zero arguments, but it can be a 
            method of a class or instance.

        interval (int): Number of seconds to wait between two calls to
            *func*.

        followup (str): What to do after the python function was called.
            Can take the following values: 

            - ``refresh`` submits and reloads the current page (default),
            - ``none`` does nothing,
            - ``forward`` submits the current page and moves forward,
            - ``backward`` submits the current page and moves backward,
            - ``jump>page_name`` submits the current page and triggers
              a jump to a page with the name 'page_name'
            - ``custom`` executes custom JavaScript. If you choose this 
              option, you must supply your custom JavaScript through the
              argument *custom_js*.

        submit_first (bool): If True, the current values of all input
            elements on the current page will be saved on button click,
            before *func* is called. This way, these values will be
            available in *func* through :attr:`.ExperimentSession.values`, 
            if func has access to the ExperimentSession object.
            See Example 3. Defaults to True.

        reset_delay (bool): If *True*, the delay will start from the 
            beginning every time the page is reloaded, refreshed, or
            revisited. Defaults to *False*.

        custom_js (str): Custom JavaScript to execute after the python
            function specified in *func* was called. Only takes effect,
            if *followup* is set to 'custom'.
    
    Examples:

        The callback on the first page will trigger every 10 seconds.
        It will print the experiment id to the terminal::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):

                def on_exp_access(self):
                    self += al.RepeatedCallback(func=self.print_expid, interval=10)

                def print_expid(self):
                    print(self.exp.exp_id)
    """

    web_widget = None
    should_be_shown = False

    #: Javascript template
    js_template = jinja_env.get_template("js/repeatedcallback.js.j2")

    def __init__(self, func: callable, interval: int, followup: str = "none", submit_first: bool = True, custom_js: str = ""):
        super().__init__()
        self.func = func
        self.interval = interval
        self.submit_first = submit_first
        self.url = None
        self.followup = followup
        self.custom_js = custom_js

    def prepare_web_widget(self):
        # docstring inherited
        self._js_code = []
        super().prepare_web_widget()
        self.url = self.exp.ui.add_callable(self.func)

        d = {}
        d["url"] = self.url
        d["followup"] = self.followup
        d["interval"] = self.interval
        d["submit_first"] = self.submit_first
        d["custom_js"] = self.custom_js
        d["set_data_url"] = self.exp.ui.set_page_data_url

        js = self.js_template.render(d)
        self.add_js(js)
