"""
Provides elements that make stuff happen.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from typing import Union
from typing import List
from uuid import uuid4

from ..exceptions import AlfredError
from .._helper import inherit_kwargs

from .core import jinja_env
from .core import _Choice
from .core import Row
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

        t = jinja_env.get_template("submittingbuttons.js.j2")
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
