"""
Provides elements that allow participant input.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

import re
import string

from typing import Union
from typing import Tuple
from typing import List
from pathlib import Path

import bleach
from emoji import emojize
import cmarkgfm
from cmarkgfm.cmark import Options as cmarkgfmOptions

from ..exceptions import AlfredError
from .._helper import inherit_kwargs

from .core import jinja_env
from .core import Element
from .core import InputElement
from .core import _Choice
from .core import ChoiceElement

@inherit_kwargs
class TextEntry(InputElement):
    """
    Provides a text entry field.

    Args:
        placeholder: Placeholder text, displayed inside the input field.
        {kwargs}

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.TextEntry(toplab="Enter here", name="el1")

    """

    element_template = jinja_env.get_template("html/TextEntryElement.html.j2")

    def __init__(
        self,
        placeholder: str = None,
        **kwargs,
    ):
        """Constructor method."""
        super().__init__(**kwargs)

        self._placeholder = placeholder if placeholder is not None else ""

    @property
    def input(self) -> str:
        # docstring inherited
        return self._input
    
    @input.setter
    def input(self, value):
        self._input = bleach.clean(value) # sanitizing input

    @property
    def placeholder(self) -> str:
        """str: Placeholder text, displayed inside the input field."""
        return self._placeholder

    @property
    def template_data(self):
        
        d = super().template_data
        d["placeholder"] = self.placeholder
        return d

    @property
    def codebook_data(self):
        
        data = super().codebook_data
        data["placeholder"] = self.placeholder
        return data

@inherit_kwargs
class TextArea(TextEntry):
    """
    A text area for long text input.

    Args:
        nrows: Initial height of the text area in number of rows.
        {kwargs}

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.TextArea(toplab="Enter here", name="el1")

    """

    element_template = jinja_env.get_template("html/TextAreaElement.html.j2")

    def __init__(self, nrows: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.area_nrows = nrows

    @property
    def template_data(self):
        
        d = super().template_data
        d["area_nrows"] = self.area_nrows
        return d

@inherit_kwargs
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
        {kwargs}

    Examples:

        Example for a RegEntry element that will match any input:

            >>> import alfred3 as al
            >>> regentry = al.RegEntry("Enter text here", pattern=r".*", name="reg1")
            >>> regentry
            RegEntry(name='reg1')

    """

    def __init__(self, pattern: str = r".*", match_hint: str = None, **kwargs):
        super().__init__(**kwargs)

        #: Compiled regular expression pattern to be matched on
        #: participant input to this element
        self.pattern: re.Pattern = re.compile(pattern)
        self._match_hint = match_hint  # documented in getter property

    def validate_data(self):
        
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
        
        else:
            return True

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
        
        d = super().codebook_data
        d["regex_pattern"] = self.pattern.pattern
        return d


@inherit_kwargs(exclude=["force_input", "pattern"])
class PasswordEntry(RegEntry):
    """
    Displays a password field.

    The password field is force-entry by default.
    
    Args:
        password (str): Password string to match against user input.
            Can be a simple string, or a regular expression.
        
        force_input (bool): If `True`, users can  only progress to the next page
            if they enter data into this field. Note that a
            :class:`.NoValidationSection` or similar sections might
            overrule this setting. Defaults to *True*.

        {kwargs}
    """

    element_template = jinja_env.get_template("html/PasswordEntry.html.j2")

    def __init__(self, password: str, force_input: bool = True, **kwargs):
        super().__init__(pattern=password, force_input=force_input, **kwargs)


@inherit_kwargs
class NumberEntry(TextEntry):
    """
    Displays an input field which only accepts numerical input.

    Args:
        decimals: Accepted number of decimals (0 as default).
        min: Minimum accepted entry value.
        max: Maximum accepted entry value.
        decimal_signs: Tuple of accepted decimal signs. Defaults to
            ``(",", ".")``, i.e. by default, both a comma and a dot are
            interpreted as decimal signs.
        match_hint: Specialized match hint for this element. You can
            use the placeholders ``{{min}}``, ``{{max}}``, ``{{ndecimals}}``,
            and ``{{decimal_signs}}``. To customize the match hint for
            all NumberEntry elements, change the respective setting
            in the config.conf.
        {kwargs}

    Examples:

        >>> import alfred3 as al
        >>> numentry = al.NumberEntry("enter here", name="num1")
        >>> numentry
        NumberEntry(name='num1')

    """

    def __init__(
        self,
        ndecimals: int = 0,
        min: Union[int, float] = None,
        max: Union[int, float] = None,
        decimal_signs: Union[str, tuple] = (",", "."),
        match_hint: str = None,
        **kwargs,
    ):

        self.ndecimals: int = ndecimals  # documented in getter property
        self.decimal_signs: Tuple[str] = decimal_signs  # documented in getter property
        self.min = min  # documented in getter property
        self.max = max  # documented in getter property
        self._match_hint = match_hint  # documented in getter property
        super().__init__(**kwargs)

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
        """Union[int, float]: Minimum value that is accepted by this element."""
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
        """Union[int, float]: Maximum value that is accepted by this element."""
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

        hint = hint.format(
            min=str(self.min), 
            max=str(self.max), 
            decimal_signs=signs, 
            ndecimals=str(self.ndecimals)
            )

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
        
        return self._input

    @input.setter
    def input(self, value: str):
        value = str(value)
        for sign in self.decimal_signs:
            value = value.replace(sign, ".")
        self._input = value

    def validate_data(self):
        
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
        
        data = super().codebook_data

        data["ndecimals"] = self.ndecimals
        data["decimal_signs"] = " ".join(self.decimal_signs)
        data["min"] = self.min
        data["max"] = self.max

        return data

@inherit_kwargs
class SingleChoice(ChoiceElement):
    """
    Radio buttons for choosing a single option.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        default: The *default* argument of single choice elements is an
            integer, indicating which choice should be selected by
            default. Counting of choices starts at 1.
        {kwargs}

    Notes:
        This element saves and returns not a single value, but a 
        dictionary of values. Each choice is represented by a key, and
        the corresponding value is *True*, if the choice was selected and
        *False* otherwise.

        The keys are of the form "choice{{i}}", where {{i}} is a placeholer
        for the number of the choice.
        

    Examples:
        A simple SingleChoice element::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.SingleChoice("Yes", "No", name="c1")
        
        Accessing the input to a SingleChoice element::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.SingleChoice("Yes", "No", name="c1")
                
                def on_first_hide(self):
                    
                    # access values
                    c1_yes = self.exp.values["c1"]["choice1"]
                    c1_no = self.exp.values["c1"]["choice2"]

                    # log values
                    self.log.info(f"'Yes' selected: {{c1_yes}}")
                    self.log.info(f"'No' selected: {{c1_no}}")
        

    """

    # Documented at :class:`.ChoiceElement`
    type: str = "radio"

    def define_choices(self) -> List[_Choice]:
        
        choices = []
        for i, label in enumerate(self.choice_labels, start=1):
            choice = _Choice()

            if isinstance(label, Element):
                choice.label = label.web_widget
            else:
                if self.emojize:
                    label = emojize(str(label), use_aliases=True)
                choice.label = cmarkgfm.github_flavored_markdown_to_html(str(label), options=cmarkgfmOptions.CMARK_OPT_UNSAFE)
            choice.type = "radio"
            choice.value = i
            choice.name = self.name
            choice.id = f"{self.name}_choice{i}"
            if choice.id in self.exp.root_section.all_elements:
                msg = (
                    f"You have a SingleChoice-type element of name {self.name}, which means "
                    f"that the name '{choice.id}' must be reserved. Please check if you are using "
                    "it for any other element."
                )
                raise AlfredError(msg)

            choice.label_id = f"{choice.id}-lab"
            choice.disabled = True if self.disabled else False

            if self.input:
                choice.checked = True if int(self.input[f"choice{choice.value}"]) == i else False
            elif self.default is not None:
                choice.checked = True if self.default == i else False

            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)
        return choices

    @property
    def default_no_input_hint(self) -> str:
        # docstring inherited
        return self.experiment.config.get("hints", "no_inputSingleChoice")
    
    def set_data(self, d):
        
        # Important: We need to have a check that ensures that the
        # generated name for the value of each choice is not used by
        # any other name in the experiment.
        # For this element, we implement it in the *define_choices* 
        # method.
        if not self.name in d:
            return

        chosen_option = d.get(self.name)
        for choice in self.choices:
            self._input[f"choice{choice.value}"] = str(choice.value) == chosen_option


@inherit_kwargs
class MultipleChoice(ChoiceElement):
    """
    Checkboxes for choosing multiple options.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        min, max: Minimum (maximum) number of choices that need to be
            selected, if any are selected (does not imply
            *force_input=True*).
        select_hint: Hint to be displayed, if the requirement of
            minimum or maximum number of selected fields is not reached.
            Defaults to the experiment-wide value specified in
            config.conf.
        default: Can be a single integer, or a list of integers which
            indicate the choices that should be selected by default.
            Counting starts at 1.
        {kwargs}

    Notes:
        This element saves and returns not a single value, but a 
        dictionary of values. Each choice is represented by a key, and
        the corresponding value is *True*, if the choice was selected and
        *False* otherwise.

        The keys are of the form "choice{{i}}", where {{i}} is a placeholer
        for the number of the choice.

    See Also:
        See :class:`.SingleChoice` for an example that shows how to access
        data from a normal choice-type element within the experiment.
    
    Examples:
        A multiple choice element with three options::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.MultipleChoice("Yes", "No", "Maybe", name="m1")

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

        #: See documentation of initialization arguments
        self.min: int = min if min is not None else 0

        #: See documentation of initialization arguments
        self.max: int = max if max is not None else len(self.choice_labels)

        self._select_hint = select_hint  # documented in getter method

        if isinstance(default, int):
            self.default = [default]
        elif default is not None and not isinstance(default, list):
            raise ValueError(
                "Default for MultipleChoice must be a list of integers, indicating the default choices."
            )
        else:
            self.default = default

    @property
    def select_hint(self) -> str:
        """
        str: Hint for participants. Displayed, if the number of selected
        choices does not fulfill the requirements of the *min* and *max*
        number.
        """
        if self._select_hint:
            return self._select_hint
        else:
            msg = self.experiment.config.get("hints", "select_MultipleChoice")
            return msg.format(min=self.min, max=self.max)

    def validate_data(self) -> bool:
        checked_values = {k: v for k, v in self.input.items() if v}

        if not self.should_be_shown:
            return True

        elif self.force_input and not checked_values:
            self.hint_manager.post_message(self.no_input_hint)
            return False

        elif not (self.min <= sum(list(self.input.values())) <= self.max):
            return False

        else:
            return True

    def set_data(self, d):
        
        # Important: We need to have a check that ensures that the
        # generated name for the value of each choice is not used by
        # any other name in the experiment.
        # For this element, we implement it in the *define_choices* 
        # method.
        for choice in self.choices:

            value = d.get(choice.name, None)
            self._input[f"choice{choice.value}"] = str(choice.value) == value

    def define_choices(self):
        
        choices = []
        for i, label in enumerate(self.choice_labels, start=1):
            choice = _Choice()

            if isinstance(label, Element):
                choice.label = label.web_widget
            else:
                if self.emojize:
                    label = emojize(str(label), use_aliases=True)
                choice.label = cmarkgfm.github_flavored_markdown_to_html(str(label), options=cmarkgfmOptions.CMARK_OPT_UNSAFE)
            choice.type = "checkbox"
            choice.value = i
            choice.id = f"{self.name}_choice{i}"

            if choice.id in self.exp.root_section.all_elements:
                msg = (
                    f"You have a MultipleChoice-type element of name {self.name}, which means "
                    f"that the name '{choice.id}' must be reserved. Please check if you are using "
                    "it for any other element."
                )
                raise AlfredError(msg)

            choice.name = choice.id
            choice.label_id = f"{choice.id}-lab"
            choice.css_class = f"choice-button choice-button-{self.name}"

            if self.debug_enabled:
                choice.checked = True if i <= self.max else False
            elif self.input:
                choice.checked = True if self.input[f"choice{choice.value}"] is True else False
            elif self.default:
                choice.checked = True if i in self.default else False

            choices.append(choice)
        return choices

    @property
    def default_no_input_hint(self) -> str:
        # docstring inherited
        return self.experiment.config.get("hints", "no_inputMultipleChoice")


@inherit_kwargs
class SingleChoiceList(SingleChoice):
    """
    A dropdown list, allowing selection of one option.

    Args:
        {kwargs}

    Notes:
        The SingleChoiceList's default value defaults to "1" due to its
        design. A typical way to remove meaning from this default is
        to make the fist choice a no-choice option (see examples).

        Also, note that the SingleChoiceList uses a different data
        representation than other choice elements. This is due to the
        fact that a typical use case for a SingleChoiceList is selection
        from a long list of possible choices. Also, choices can only be
        strings, while other choice elements also allow, for example, images.

        For this reason, the SingleChoiceList does not save a True/False
        status for each choice, but simply the label of the selected choice
        as a string. 

    Examples:
        A single choice list with a no-choice option as first option::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.SingleChoiceList(
                        "-no selection-", "choi1", "choi2", "choi3",
                         name="sel1"
                         )
        
        Accessing the value of a SingleChoiceList::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.SingleChoiceList(
                        "-no selection-", "choi1", "choi2", "choi3",
                         name="sel1"
                         )
                
                def on_first_hide(self):
                    selection = self.exp.values["sel1"] # accesses selection
                    self.log.info(selection) # logs selection string

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/SelectElement.html.j2")

    # Documented at :class:`.SingleChoice`
    type = "select_one"

    def __init__(self, *choice_labels, default: int = 1, **kwargs):
        super().__init__(*choice_labels, default=default, **kwargs)

    
    def define_choices(self) -> List[_Choice]:
        
        choices = []
        for i, label in enumerate(self.choice_labels, start=1):
            choice = _Choice()

            if not isinstance(label, str):
                raise TypeError(f"Choice label in {type(self).__name__} must be string, not {type(label)}.")

            choice.label = label
            choice.type = "radio"
            choice.value = choice.label
            choice.name = self.name
            choice.id = f"{self.name}_choice{i}"
            if choice.id in self.exp.root_section.all_elements:
                msg = (
                    f"You have a SingleChoice-type element of name {self.name}, which means "
                    f"that the name '{choice.id}' must be reserved. Please check if you are using "
                    "it for any other element."
                )
                raise AlfredError(msg)

            choice.label_id = f"{choice.id}-lab"
            choice.disabled = True if self.disabled else False

            if self.input:
                choice.checked = True if int(self.input[f"choice{choice.value}"]) == i else False
            elif self.default is not None:
                choice.checked = True if self.default == i else False

            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)
        return choices


    def set_data(self, d):
        if not self.disabled:
            try:
                self.input = d[self.name]
            except KeyError:
                self.log.debug(f"No data for {self} found in data dictionary. Moving on.")
                pass


@inherit_kwargs
class MultipleChoiceList(MultipleChoice):
    """
    A :class:`.MultipleChoice` element, displayed as list.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        size: The vertical height of the list. The unit is the number
            of choices to be displayed without scrolling. Note that some
            browsers do not adhere to this unit exactly.
        {kwargs}

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.MultipleChoiceList("choi1", "choi2", "choi3", name="sel1")

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/SelectElement.html.j2")

    # Documented at :class:`.SingleChoice`
    type = "multiple"

    def __init__(self, *choice_labels, size: int = None, **kwargs):
        super().__init__(*choice_labels, **kwargs)
        self.size = size

    @property
    def template_data(self):
        
        d = super().template_data
        d["size"] = self.size
        return d

    def set_data(self, d):
        
        name_map = {str(choice.value): choice.name for choice in self.choices}
        val = d.get(self.name, None)
        val_name = name_map[val]

        for choice in self.choices:
            if choice.name == val_name:
                self.input[choice.name] = True
            else:
                self.input[choice.name] = False

@inherit_kwargs
class SingleChoiceButtons(SingleChoice):
    """
    A prettier :class:`.SingleChoice` element with buttons instead of
    radio inputs.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.

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
            will be repeated for remaining buttons. Advanced users can
            supply their own CSS classes for button-styling.

        button_round_corners: A boolean switch to toggle whether buttons
            should be displayed with  rounded corners (*True*). 

        {kwargs}

    Notes:

        - The *align* parameter does not affect the alignment of choice
          labels.

    See Also:
        See :class:`.SingleChoice` for an example that shows how to access
        data from a normal choice-type element within the experiment.

    Examples:
        A single choice button element with three choices::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.SingleChoiceButtons("Yes", "No", "maybe", name="b1")

    """

    element_template = jinja_env.get_template("html/ChoiceButtons.html.j2")

    #: A boolean switch to toggle whether buttons should be layoutet as
    #: a connected toolbar (*True*), or as separate neighbouring buttons
    #: (*False*, default).
    button_toolbar: bool = False

    #: CSS class for the button group
    button_group_class: str = "choice-button-group"

    def __init__(
        self,
        *choice_labels,
        button_width: Union[str, list] = "equal",
        button_style: Union[str, list] = "btn-outline-dark",
        button_round_corners: bool = True,
        **kwargs,
    ):
        super().__init__(*choice_labels, **kwargs)
        self.button_width: Union[str, list] = button_width
        self.button_style: Union[str, list] = button_style
        self.button_round_corners: bool = button_round_corners

    @property
    def button_style(self) -> Union[str, list]:
        """Union[str, list]: See documentation for the initialization argument."""
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
    def template_data(self) -> dict:
        
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

@inherit_kwargs
class SingleChoiceBar(SingleChoiceButtons):
    """
    A variation of :class:`.SingleChoiceButtons`, which is displayed as
    a toolbar of connected buttons.

    Args:
        {kwargs}

    See Also:
        See :class:`.SingleChoice` for an example that shows how to access
        data from a normal choice-type element within the experiment.

    Examples:
        A single choice bar with three options::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.SingleChoiceBar("Yes", "No", "Maybe", name="b1")
    """

    # Documented at :class:`.SingleChoiceButtons`
    button_group_class = "choice-button-bar"

    # Documented at :class:`.SingleChoiceButtons`
    button_toolbar = True


@inherit_kwargs
class MultipleChoiceButtons(MultipleChoice, SingleChoiceButtons):
    """
    A prettier :class:`.MultipleChoice` element with buttons instead of
    checkbox inputs.

    To make them distinct from single choice buttons, multiple choice
    buttons don't have rounded corners by default.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        min, max: Minimum (maximum) number of choices that need to be
            selected, if any are selected (does not imply
            *force_input=True*).
        select_hint: Hint to be displayed, if the requirement of
            minimum or maximum number of selected fields is not reached.
            Defaults to the experiment-wide value specified in
            config.conf.
        default: Can be a single integer, or a list of integers which
            indicate the choices that should be selected by default.
            Counting starts at 1.
        
        {kwargs}

    See Also:
        See :class:`.SingleChoice` for an example that shows how to access
        data from a normal choice-type element within the experiment.

    Examples:
        Multiple choice buttons with three options::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.MultipleChoiceButtons("Yes", "No", "Maybe", name="m1")

    """

    def __init__(self, *choice_labels, button_round_corners: bool = False, **kwargs):
        super().__init__(*choice_labels, button_round_corners=button_round_corners, **kwargs)

@inherit_kwargs
class MultipleChoiceBar(MultipleChoiceButtons):
    """
    A variation of :class:`.MultipleChoiceButtons`, which is displayed as
    a toolbar of connected buttons.

    Args:
        {kwargs}

    See Also:
        See :class:`.SingleChoice` for an example that shows how to access
        data from a normal choice-type element within the experiment.

    Examples:
        A multiple choice bar with three options::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo_page"

                def on_exp_access(self):
                    self += al.MultipleChoiceBar("Yes", "No", "Maybe", name="b1")

    """

    # Documented at :class:`.SingleChoiceButtons
    button_group_class: str = "choice-button-bar"

    # Documented at :class:`.SingleChoiceButtons
    button_toolbar: bool = True

    # Documented at :class:`.SingleChoiceButtons
    button_round_corners: bool = False

@inherit_kwargs
class SelectPageList(SingleChoiceList):
    """
    A :class:`.SingleChoiceList`, automatically filled with page names.

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
        {kwargs}

    Notes:
        This is mostly a utility element for the implementation of
        :class:`.JumpList`.

    Examples:

        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo1(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    self += al.SelectPageList(name="select_page")

            @exp.member()
            class Target(al.Page):
                name = "demo2"

    """

    def __init__(
        self,
        scope: str = "exp",
        include_self: bool = False,
        check_jumpto: bool = True,
        check_jumpfrom: bool = True,
        show_all_in_scope: bool = True,
        display_page_name: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.scope = scope
        self.check_jumpto = check_jumpto
        self.check_jumpfrom = check_jumpfrom
        self.show_all_in_scope = show_all_in_scope
        self.include_self = include_self
        self.display_page_name = display_page_name

    def _determine_scope(self) -> List[str]:
        """
        Determines, which pages belong to the scope of the element *and*
        should appear in the dropdown.

        Returns:
            List[str]: List of page names that are in the elements scope
                and should be shown in the dropdown.
        """

        if self.scope in ["experiment", "exp"]:
            scope = list(self.experiment.root_section.members["_content"].all_pages.values())
        else:
            try:
                target_section = self.experiment.root_section.all_sections[self.scope]
                scope = list(target_section.all_pages.values())
            except AttributeError:
                raise AlfredError("Parameter 'scope' must be a section name or 'exp'.")

        choice_labels = []
        if not self.show_all_in_scope:
            for page in scope:
                if page.section.allow_jumpto and page.should_be_shown:
                    choice_labels.append(page.name)
        else:
            choice_labels = [page.name for page in scope]

        if not self.include_self:
            try:
                choice_labels.remove(self.name)
            except ValueError:
                self.log.debug("ValueError ignored.")
                pass

        return choice_labels

    def define_choices(self) -> List[_Choice]:
        
        choices = []
        for i, page_name in enumerate(self.choice_labels, start=1):
            choice = _Choice()

            choice.label = self._choice_label(page_name)
            choice.type = "radio"
            choice.value = page_name
            choice.name = self.name
            choice.id = f"choice{i}-{self.name}"
            choice.label_id = f"{choice.id}-lab"
            choice.disabled = True if self.disabled else self._jump_forbidden(page_name)
            choice.checked = self._determine_check(i) if not choice.disabled else False
            choice.css_class = f"choice-button choice-button-{self.name}"

            choices.append(choice)

        return choices

    def _jump_forbidden(self, page_name: str) -> bool:
        """
        Returns:
            bool: True, if jumping to the target page or from the
            current page is forbidden. Also True, if the target page
            should not be shown.
        """
        target_page = self.experiment.root_section.all_pages[page_name]

        conditions = [True]  # list of conditions. True means that jumping is allowed

        # disable choice if the target page can't be jumped to
        if self.check_jumpto:
            jump_allowed = target_page.section.allow_jumpto
            conditions.append(jump_allowed)

        # disable choice if self can't be jumped from
        if self.check_jumpfrom:
            jump_allowed = self.page.section.allow_jumpfrom
            conditions.append(jump_allowed)

        conditions.append(target_page.should_be_shown)

        return not all(conditions)

    def _choice_label(self, page_name: str) -> str:
        """
        Returns:
            str: A shortened version of the *page* name, if its length
            exceeds 35 characters.
        """
        target_page = self.experiment.root_section.all_pages[page_name]
        # shorten page title for nicer display
        page_title = target_page.title
        if len(page_title) > 35:
            page_title = page_title[:35] + "..."
        pname = f" (name='{page_name}')" if self.display_page_name else ""
        return f"{page_title}" + pname

    def _determine_check(self, i: int) -> bool:
        """
        For a given choice option, this method determines, whether it
        should be marked as checked by default.

        If the experiment is started in debug mode, the current page is
        marked as checked.

        Returns:
            bool: *True*, if the choice option with index *i* should be
            checked.

        """

        # set default value
        if self.default == i:
            checked = True
        elif self.input == self.choice_labels[i-1]:
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
