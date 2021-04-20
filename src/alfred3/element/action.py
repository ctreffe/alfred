"""
Provides elements that make stuff happen.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from typing import Union
from typing import List
from uuid import uuid4

import cmarkgfm
from cmarkgfm.cmark import Options as cmarkgfmOptions
from emoji import emojize

from ..exceptions import AlfredError
from .._helper import inherit_kwargs

from .core import jinja_env
from .core import _Choice
from .core import Row
from .core import Element
from .misc import JavaScript
from .input import SingleChoiceButtons
from .input import SingleChoiceList
from .input import SelectPageList

@inherit_kwargs
class SubmittingButtons(SingleChoiceButtons):
    """
    SingleChoiceButtons that trigger submission of the current page
    on click.

    Args:
        {kwargs}

    Examples:
        Using submitting buttons together with the
        :class:`.HideNavigation` element::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):

                    self += al.HideNavigation()
                    self += al.SubmittingButtons("choice1", "choice2", name="b1")

    """

    def __init__(self, *choice_labels, **kwargs):
        super().__init__(*choice_labels, **kwargs)

    def added_to_page(self, page):
        
        super().added_to_page(page)

        t = jinja_env.get_template("js/submittingbuttons.js.j2")
        js = t.render(name=self.name)

        page += JavaScript(code=js)

@inherit_kwargs
class JumpButtons(SingleChoiceButtons):
    """
    SingleChoiceButtons that trigger jumps to specific pages on click.

    Each button can target a different page.

    Args:
        *choice_labels: Tuples of the form ``("label", "target_name")``,
            where "label" is the text that will be displayed and
            "target_name" is the name of the page that the experiment
            will jump to on click of the button.

        {kwargs}

    Attributes:
        targets (str): List of target page names.

    Examples:
        Simple jump buttons::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo1(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    self += al.JumpButtons(
                        ("jump to demo2", "demo2"),
                        ("jump to demo3", "demo3"),
                        name="jump1"
                        )

            @exp.member
            class Demo2(al.Page):
                name = "demo2"

            @exp.member
            class Demo3(al.Page):
                name = "demo3"

        Jump buttons with target page taken from the input on a previous
        page, using the :meth:`.Page.on_first_show` hook::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo1(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    self += al.TextEntry(toplab="Enter target page name", name="text1")

            @exp.member
            class Demo2(al.Page):
                name = "demo2"

                def on_first_show(self):
                    target = self.exp.values.get("text1")
                    self += al.JumpButtons(("jump to target", target), name="jump1")

            @exp.member
            class Demo3(al.Page):
                name = "demo3"

    """

    #: JavaScript template for the code that submits the form on click
    js_template = jinja_env.get_template("js/jumpbuttons.js.j2")

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
        if not self.should_be_shown:
            return True
        
        cond1 = bool(self.input) if self.force_input else True
        return cond1

@inherit_kwargs
class DynamicJumpButtons(JumpButtons):
    """
    JumpButtons, where the target pages depend on the input to
    other elements on the same page.

    Args:
        *choice_labels: Tuples of the form ``("label", "element_name")``,
            where "label" is the text that will be displayed and
            "element_name" is the name of the element on the *same page*,
            whose input value will be inserted as the name of the target
            page.

        {kwargs}

    Attributes:
        targets (str): List of target page names.

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo1(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    self += al.TextEntry(toplab="Enter a target page", name="text1")
                    self += al.DynamicJumpButtons(("Jump", "text1"), name="jump1")

            @exp.member
            class Demo2(al.Page):
                name = "demo2"

            @exp.member
            class Demo3(al.Page):
                name = "demo3"

    """

    # Documented at :class:`.JumpButtons`
    js_template = jinja_env.get_template("js/dynamic_jumpbuttons.js.j2")

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

@inherit_kwargs
class JumpList(Row):
    """
    Allows participants to select a page from a dropdown menu and jump
    to it.

    Args:
        scope: Can be 'exp', or a section name. If *scope* is 'exp', all
            pages in the experiment are listed as choices. If *scope* is
            a section name, all pages in that section are listed.
        include_self: Whether to include the current page in the list,
            if it is in scope.
        check_jumpto: If *True* (default), pages that cannot be jumped
            to will be marked as disabled options. The evaluation is
            based on the :attr:`.Section.allow_jumpto` attribute of
            each page's direct parent section (and only that section).
        check_jumpfrom: If *True*, the element will check, if the
            current page can be left via jump. If not, all pages in the
            list will be marked as disabled options.
        show_all_in_scope: If *True* (default), all pages in the scope
            will be shown, including those that cannot be jumped to.
        display_page_name: If *True*, the page name will be displayed
            in the select list. Defaults to *True*.
        label: Label to display on the jump button.
        button_style: Style of the jump button. See
            :class:`.SingleChoiceButtons` for more details on this
            argument.
        button_round_corners: Boolean, determining whether the button
            should have rounded corners.
        debugmode: Boolean switch, telling the JumpList whether it
            should operate in debug mode.
        
        {kwargs}

    Notes:
        Different from other input-type elements, the JumpList does not
        have to be named.

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo1(al.Page):
                name = "demo2"

                def on_exp_access(self):
                    self += al.JumpList()

            @exp.member
            class Demo2(al.Page):
                name = "demo2"

    """

    def __init__(
        self,
        scope: str = "exp",
        include_self: bool = False,
        check_jumpto: bool = True,
        check_jumpfrom: bool = True,
        show_all_in_scope: bool = True,
        label: str = "Jump",
        button_style: Union[str, list] = "btn-dark",
        button_round_corners: bool = False,
        debugmode: bool = False,
        display_page_name: bool = True,
        **kwargs,
    ):

        random_name = "jumplist_" + uuid4().hex
        name = kwargs.get("name", random_name)
        select_name = name + "_select"
        btn_name = name + "_btn"
        select = SelectPageList(
            scope=scope,
            include_self=include_self,
            name=select_name,
            check_jumpto=check_jumpto,
            check_jumpfrom=check_jumpfrom,
            show_all_in_scope=show_all_in_scope,
            display_page_name=display_page_name
        )
        btn = DynamicJumpButtons(
            (label, select_name),
            name=btn_name,
            button_style=button_style,
            button_round_corners=button_round_corners,
        )
        super().__init__(select, btn, **kwargs)

        self.layout.width_sm = [10, 2]
        self.debugmode = debugmode

    def prepare_web_widget(self):
        
        super().prepare_web_widget()

        if not self.page.section.allow_jumpfrom:
            # disable button (disabling the list is controlled via init arguments of the list)
            self.elements[1].disabled = True

        if self.debugmode:
            for el in self.elements:
                el.disabled = False


@inherit_kwargs
class Button(Element):
    """
    A button that triggers execution of a python function on click.
    
    Args:
        text (str): Button text

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
        
        button_style (str): Can be used for quick color-styling, using
            Bootstraps default color keywords: btn-primary, btn-secondary,
            btn-success, btn-info, btn-warning, btn-danger, btn-light,
            btn-dark. You can also use the "outline" variant to get
            outlined buttons (eg. "btn-outline-secondary"). Advanced users can
            supply their own CSS classes for button-styling. Defaults
            to "btn-primary".
        
        button_round_corners (bool): A boolean switch to toggle whether 
            the button should be displayed with rounded corners. Defaults 
            to False. 
        
        button_block (bool): A boolean switch to toggle whether the button
            should take up all horizontal space that is available. Can be
            quite useful when arranging buttons in :class:`.Row`s. 
            Defaults to False.
        
        custom_js (str): Custom JavaScript to execute after the python
            function specified in *func* was called. Only takes effect,
            if *followup* is set to 'custom'.

        {kwargs}
    
    Notes:

        Note that by default, the Button will not save data itself. If
        you wish to save information about button clicks, you can utilize
        the :attr:`.ExperimentSession.adata` dictionary in the button's
        callable. See Example 4.

        .. warning:: This element is very powerful. Remember that with great
            power comes great responsibility. Be aware that the callable
            *func* will be executed *every time* the button is clicked.
    
    Examples:

        Example 1: A minimal example that will print some text to your terminal
        window on button click::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):

                def on_exp_access(self):
                    self += al.Button("Demo Button", func=self.demo_function)
                
                def demo_function(self):
                    print("\\nThis is a demonstration")
                    print(self.exp.exp_id)
                    print("\\n")
        
        Example 2: An example with a jump after the function call::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):

                def on_exp_access(self):
                    self += al.Button("Demo Button", func=self.demo_function, followup="jump>page3")
            
                def demo_function(self):
                    print("\\nThis is a demonstration")
                    print(self.exp.exp_id)
                    print("\\n")

            exp += al.Page(title="Page 2", name="page2")
            exp += al.Page(title="Page 3", name="page3")

        
        Example 3: An example that uses values entered on the current page::
            
            import alfred3 as al
            exp = al.Experiment()


            @exp.member
            class Demo(al.Page):
                
                def on_exp_access(self):
                    self += al.TextEntry(leftlab="Enter", name="entry1")
                    self += al.Button("Demo Button", func=self.demo_function)

                def demo_function(self):
                    print("\\nThis is a demonstration")
                    print(self.exp.exp_id)
                    print(self.exp.values["entry1"])
                    print("\\n")
        
        Example 4: An example that saves a count of how often the button
        was clicked::
            
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                
                def on_exp_access(self):
                    self += al.Button("Demo Button", func=self.demo_function)

                def demo_function(self):
                    print("\\nThis is a demonstration")
                    
                    if "demo_button" in self.exp.adata:
                        self.exp.adata["demo_button"] += 1
                    else:
                        self.exp.adata["demo_button"] = 1
                        
                    print("\\n")


    """
    element_template = jinja_env.get_template("html/ActionButtonElement.html.j2")
    js_template = jinja_env.get_template("js/actionbutton.js.j2")

    def __init__(
        self, 
        text: str, 
        func: callable, 
        followup: str = "refresh",
        submit_first: bool = True,
        button_style: str = "btn-primary",
        button_round_corners: bool = False, 
        button_block: bool = False,
        custom_js: str = "",
        **kwargs):
        super().__init__(**kwargs)
        
        self.func = func
        self.submit_first = submit_first
        self.followup = followup
        self.url = None
        self.text = text
        self.custom_js = custom_js

        if not followup in {"refresh", "forward", "backward", "none", "custom"} and not followup.startswith("jump>"):
            raise ValueError(f"{followup} is an inappropriate value for 'followup'.")

        if self.followup == "custom" and not self.custom_js:
            raise ValueError("If you set 'followup' to 'custom', you must specify custom Javascritp to run.")

        self.button_style = button_style
        self.button_round_corners = button_round_corners
        self.button_block = button_block
    
    @property
    def template_data(self):
        d = super().template_data
        text = emojize(self.text, use_aliases=True)
        text = cmarkgfm.github_flavored_markdown_to_html(text, options=cmarkgfmOptions.CMARK_OPT_UNSAFE)
        d["text"] = text
        d["button_block"] = "btn-block" if self.button_block else ""
        d["button_style"] = self.button_style
        return d
    
    def prepare_web_widget(self):
        self.url = self.exp.ui.add_callable(self.func)

        # Javascript part
        self._js_code = []
        d = {}
        d["url"] = self.url
        d["expurl"] = f"{self.exp.ui.basepath}/experiment"
        d["followup"] = self.followup
        d["name"] = self.name
        d["submit_first"] = self.submit_first
        js = self.js_template.render(d)
        self.add_js(js)

        # Round corners part
        if self.button_round_corners:
            self._css_code = []
            css = f"#{ self.name } {{border-radius: 1rem;}}"
            self.add_css(css)
    