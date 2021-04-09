"""
Provides elements that don't fit into the other categories.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

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
            raise ValueError("You can only specify one of 'code', 'url', or 'path'.")

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
            raise ValueError("You can only specify one of 'code', 'url', or 'path'.")

    @property
    def js_code(self):
        if not self.code:
            return []
        
        if self.path:
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
        code = "$(document).ready(function(){glob_unbind_leaving();});"
        super().__init__(code=code, priority=10)


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

    web_widget = None
    should_be_shown = False

    def __init__(self, func: callable, followup: str = "refresh"):
        super().__init__()
        self.func = func
        self.followup = followup
        self.url = None
    
    def prepare_web_widget(self):
        self._js_code = []
        super().prepare_web_widget()
        self.url = self.exp.ui.add_callable(self.func)
        
        js_template = Template("""
        $(document).ready(function () {
    
            $.get( "{{ url }}", function(data) {
                
                if ("{{ followup }}" == "refresh") {
                    move(direction="stay");
                } else if ("{{ followup }}" == "custom") {
                    {{ custom_js }}
                } else if ("{{ followup }}" != "none") {
                    move(direction="{{ followup }}");
                }
            });
            
        });
        """)
        js = js_template.render(url=self.url, followup=self.followup)
        self.add_js(js)


class RepeatedCallback(Element):

    web_widget = None
    should_be_shown = False

    def __init__(self, func: callable, submit_first: bool = True, interval: int = 1):
        super().__init__()
        self.func = func
        self.interval = interval
        self.submit_first = submit_first
        self.url = None
    
    def prepare_web_widget(self):
        self._js_code = []
        super().prepare_web_widget()
        self.url = self.exp.ui.add_callable(self.func)
        
        js_template = Template("""
        var ping = function() {
            
            {% if submit_first %}
                var data = $("#form").serializeArray();
                $.post("/callable/set_page_data", data);
            {% endif %}

            $.get( "{{ url }}" );
        };

        $(document).ready(function () {
            setInterval(ping, {{ interval }} * 1000)
        });
        """)
        js = js_template.render(url=self.url, submit_first=self.submit_first, interval=self.interval)
        self.add_js(js)