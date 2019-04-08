# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

**element** contains general baseclass :class:`.element.Element` and its' children, which can be added to
:class:`.question.CompositePage` (see table for an overview). It also contains abstract baseclasses for
different interfaces (:class:`.element.WebElementInterface`, :class:`.element.QtElementInterface`), which
must also be inherited by new child elements of :class:`.element.Element` to establish interface compatibility.

===================== ===============================================================
Name                  Description
===================== ===============================================================
TextElement           A simple text display (can contain html code)
DataElement           Element for saving Variables into Data (without display)
TextEntryElement      A singleline textedit with instruction text
TextAreaElement       A multiline textedit field with instruction text
RegEntryElement       An element which compares input with a regular expression
NumberEntryElement    An entry element for numbers
PasswordElement       An element which compares input with a predefined password
LikertMatrix          A matrix with multiple items and a predefined number of levels
LikertElement         A likert scale with n levels and different labels
SingleChoiceElement   A list of items, one of which can be selected
MultipleChoiceElement A list of items from which multiple can be selected
ImageElement          Display an image file
TripleBarChartElement Display a chart with three different bars (temporary)
===================== ===============================================================

'''
from __future__ import division
from __future__ import absolute_import

from future import standard_library
from functools import reduce
standard_library.install_aliases()
from builtins import str
from builtins import range
from past.utils import old_div
from builtins import object
import re
import string
import random
import json
from abc import ABCMeta, abstractproperty
import os
import jinja2

from .exceptions import AlfredError
from ._helper import fontsize_converter, alignment_converter
import alfred.settings as settings

from . import alfredlog
from future.utils import with_metaclass
logger = alfredlog.getLogger(__name__)


class Element(object):
    '''
    **Description:** Baseclass for every element with basic arguments.

    :param str name: Name of Element.
    :param str alignment: Alignment of element in widget container ('left' as standard, 'center', 'right').
    :param str/int fontSize: Font size used in element ('normal' as standard, 'big', 'huge', or int value setting font size in pt).
    '''

    def __init__(self, name=None, should_be_shown_filter_function=None, **kwargs):
        if not isinstance(self, WebElementInterface):
            raise AlfredError("Element must implement WebElementInterface.")

        if name is not None:
            if not re.match(r'^%s$' % '[-_A-Za-z0-9]*', name):
                raise ValueError(u'Element names may only contain following charakters: A-Z a-z 0-9 _ -')

        self._name = name

        self._question = None
        self._enabled = True
        self._showCorrectiveHints = False
        self._shouldBeShown = True
        self._shouldBeShownFilterFunction = should_be_shown_filter_function if should_be_shown_filter_function is not None else lambda exp: True

        self._alignment = kwargs.pop('alignment', 'left')
        self._fontSize = kwargs.pop('fontSize', 'normal')
        self._maximumWidgetWidth = None

        if kwargs != {}:
            raise ValueError("Parameter '%s' is not supported." % list(kwargs.keys())[0])

    @property
    def name(self):
        '''
        Property **name** marks a general identifier for element, which is also used as variable name in experimental datasets.
        Stored input data can be retrieved from dictionary returned by :meth:`.data_manager.DataManager.get_data`.
        '''
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, str):
            raise TypeError
        self._name = name

    @property
    def maximum_widget_width(self):
        return self._maximumWidgetWidth

    @maximum_widget_width.setter
    def maximum_widget_width(self, maximum_widget_width):
        if not isinstance(maximum_widget_width, int):
            raise TypeError
        self._maximumWidgetWidth = maximum_widget_width

    def added_to_page(self, q):
        from . import question
        if not isinstance(q, question.Page):
            raise TypeError()

        self._question = q

    @property
    def data(self):
        '''
        Property **data** contains a dictionary with input data of element.
        '''
        return {}

    @property
    def enabled(self):
        '''
        Property **enabled** describes a general property of all (input) elements. Only if set to True, element can be edited.

        :param bool enabled: Property setter variable.
        '''
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        if not isinstance(enabled, bool):
            raise TypeError

        self._enabled = enabled

    @property
    def can_display_corrective_hints_in_line(self):
        return False

    @property
    def alignment(self):
        return self._alignment

    @property
    def corrective_hints(self):
        return []

    @property
    def show_corrective_hints(self):
        return self._showCorrectiveHints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        self._showCorrectiveHints = bool(b)

    def validate_data(self):
        return True

    def set_should_be_shown_filter_function(self, f):
        """
        Sets a filter function. f must take Experiment as parameter
        :type f: function
        """
        self._shouldBeShownFilterFunction = f

    def remove_should_be_shown_filter_function(self):
        """
        remove the filter function
        """
        self._shouldBeShownFilterFunction = lambda exp: True

    @property
    def should_be_shown(self):
        """
        Returns True if should_be_shown is set to True (default) and all shouldBeShownFilterFunctions return True.
        Otherwise False is returned
        """
        return self._shouldBeShown and self._shouldBeShownFilterFunction(self._question._experiment)

    @should_be_shown.setter
    def should_be_shown(self, b):
        """
        sets should_be_shown to b.

        :type b: bool
        """
        if not isinstance(b, bool):
            raise TypeError("should_be_shown must be an instance of bool")
        self._shouldBeShown = b


class WebElementInterface(with_metaclass(ABCMeta, object)):
    '''
    Abstract class **WebElementInterface** contains properties and methods allowing elements to be used and displayed
    in experiments of type 'web'.
    '''

    @abstractproperty
    def web_widget(self):
        pass

    def prepare_web_widget(self):
        pass

    @property
    def web_thumbnail(self):
        return None

    def set_data(self, data):
        pass

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


class HorizontalLine(Element, WebElementInterface):
    def __init__(self, strength=1, color='black', **kwargs):
        '''
        **HorizontalLine** allows display of a simple divider in questions.

        :param int strength: Set line thickness (in pixel).
        :param str color: Set line color (color argument as string).
        '''
        super(HorizontalLine, self).__init__(**kwargs)

        self._strength = strength
        self._color = color

    @property
    def web_widget(self):

        widget = '<hr class="horizontal-line" style="%s %s">' % ('height: %spx;' % self._strength, 'background-color: %s;' % self._color)

        return widget


class ProgressBar(Element, WebElementInterface):
    def __init__(self, instruction='', bar_range=(0, 100), bar_value=50, bar_width=None, instruction_width=None, instruction_height=None, **kwargs):
        '''
        **ProgressBar** allows display of a manually controlled progress bar.
        '''
        super(ProgressBar, self).__init__(**kwargs)

        self._instruction = instruction
        self._instructionWidth = instruction_width
        self._instructionHeight = instruction_height
        self._barRange = bar_range
        self._barValue = float(bar_value)

        if bar_width:
            self._barWidth = bar_width
        else:
            self._barWidth = None

        self._progressBar = None

    @property
    def bar_value(self):
        return self._barValue

    @bar_value.setter
    def bar_value(self, value):
        self._barValue = value
        if self._progressBar:
            self._progressBar.setValue(self._barValue)
            self._progressBar.repaint()

    @property
    def web_widget(self):
        if self._barRange[1] - self._barRange[0] == 0:
            raise ValueError('bar_range in web progress bar must be greater than 0')

        widget = '<div class="progress-bar"><table class="%s" style="font-size: %spt;">' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize))

        widget = widget + '<tr><td><table class="%s"><tr><td style="%s %s">%s</td>' % (alignment_converter(self._alignment, 'container'), 'width: %spx;' % self._instructionWidth if self._instructionWidth is not None else "", 'height: %spx;' % self._instructionHeight if self._instructionHeight is not None else "", self._instruction)

        widget = widget + '<td><meter value="%s" min="%s" max="%s" style="font-size: %spt; width: %spx; margin-left: 5px;"></meter></td>' % (self._barValue, self._barRange[0], self._barRange[1], fontsize_converter(self._fontSize) + 5, self._barWidth if self._barWidth is not None else '200')

        widget = widget + '<td style="font-size: %spt; padding-left: 5px;">%s</td>' % (fontsize_converter(self._fontSize), str(int(old_div(self._barValue, (self._barRange[1] - self._barRange[0]) * 100))) + '%')

        widget = widget + '</tr></table></td></tr></table></div>'

        return widget


class TextElement(Element, WebElementInterface):
    def __init__(self, text, text_width=None, text_height=None, **kwargs):
        '''
        **TextElement** allows display of simple text labels.

        :param str text: Text to be displayed by TextElement (can contain html commands).
        :param str alignment: Alignment of TextElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Fontsize used in TextElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param int text_width: Set the width of the label to a fixed size, still allowing for word wrapping and growing height of text.
        :param int text_height: Set the height of the label to a fixed size (sometimes necessary when using rich text).
        '''
        super(TextElement, self).__init__(**kwargs)

        self._text = text
        self._textWidth = text_width
        self._textHeight = text_height
        self._textLabel = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        if self._textLabel:
            self._textLabel.setText(self._text)
            self._textLabel.repaint()

    @property
    def web_widget(self):
        widget = '<div class="text-element"><p class="%s" style="font-size: %spt; %s %s">%s</p></div>' % (alignment_converter(self._alignment, 'both'), fontsize_converter(self._fontSize), 'width: %spx;' % self._textWidth if self._textWidth is not None else "", 'height: %spx;' % self._textHeight if self._textHeight is not None else "", self._text)

        return widget


class DataElement(Element, WebElementInterface):
    def __init__(self, variable, **kwargs):
        '''
        **DataElement** returns no widget, but can save a variable of any type into experiment data.

        :param str variable: Variable to be stored into experiment data.
        '''
        super(DataElement, self).__init__(**kwargs)
        self._variable = variable

    @property
    def variable(self):
        return self._variable

    @variable.setter
    def variable(self, variable):
        self._variable = variable

    @property
    def web_widget(self):
        return ''

    @property
    def data(self):
        return {self.name: self._variable}


class InputElement(Element):
    '''
    Class **InputElement** is the base class for any element allowing data input.

    :param bool force_input: Sets user input to be mandatory (False as standard or True).
    :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.

    .. todo:: Parent class :class:`.element.Element` has method *corrective_hints()*, but not sure why this is necessary, since corrective_hints only make sense in input elements, right?
    '''

    def __init__(self, force_input=False, no_input_corrective_hint=None, debug_string=None, debug_value=None, default=None, **kwargs):
        super(InputElement, self).__init__(**kwargs)
        self._input = ''
        self._forceInput = force_input
        self._noInputCorrectiveHint = no_input_corrective_hint
        self._debugString = debug_string
        self._debugValue = debug_value

        if settings.debugmode and settings.debug.defaultValues:
            if self._debugValue:
                self._input = self._debugValue
            elif not self._debugString:
                self._input = settings.debug.get(self.__class__.__name__)
            else:
                self._input = settings._config_parser.get('debug', debug_string)

        if default is not None:
            self._input = default

    def validate_data(self):
        return not self._forceInput or not self._shouldBeShown or bool(self._input)

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and self._input == '':
            return [self.no_input_hint]
        else:
            return super(InputElement, self).corrective_hints

    @property
    def no_input_hint(self):
        if self._noInputCorrectiveHint:
            return self._noInputCorrectiveHint
        return self.default_no_input_hint

    @property
    def default_no_input_hint(self):
        if self._question and self._question._experiment:
            hints = self._question._experiment.settings.hints
            name = type(self).__name__
            noInputName = ('noInput_%s' % name).lower()
            if noInputName in hints:
                return hints[noInputName]

        logger.error("Can't access default no input hint for element %s" % self)
        return "Can't access default no input hint for element %s" % type(self).__name__

    @property
    def data(self):
        return {self.name: self._input}

    def set_data(self, d):
        if self.enabled:
            self._input = d.get(self.name, '')


class TextEntryElement(InputElement, WebElementInterface):
    def __init__(self, instruction='', no_input_corrective_hint=None, instruction_width=None, instruction_height=None, prefix=None, suffix=None, **kwargs):
        '''
        **TextEntryElement*** returns a single line text edit with an instruction text on its' left.

        :param str name: Name of TextEntryElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param int instruction_width: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instruction_height: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of TextEntryElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Font size used in TextEntryElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''
        super(TextEntryElement, self).__init__(no_input_corrective_hint=no_input_corrective_hint, **kwargs)

        self._instructionWidth = instruction_width
        self._instructionHeight = instruction_height
        self._instruction = instruction
        self._prefix = prefix
        self._suffix = suffix
        self._template = jinja2.Template('''
        <div class="text-entry-element"><table class="{{ alignment }}" style="font-size: {{ fontsize }}pt";>
        <tr><td valign="bottom"><table class="{{ alignment }}"><tr><td style="padding-right: 5px;{% if width %}width:{{width}}px;{% endif %}{% if height %}width:{{height}}px;{% endif %}">{{ instruction }}</td>
        <td valign="bottom">
        {% if prefix or suffix %}
            <div class="{% if prefix %}input-prepend {% endif %}{% if suffix %}input-append {% endif %}" style="margin-bottom: 0px;">
        {% endif %}
        {% if prefix %}
            <span class="add-on">{{prefix}}</span>
        {% endif %}
        <input class="text-input" type="text" style="font-size: {{ fontsize }}pt; margin-bottom: 0px;" name="{{ name }}" value="{{ input }}" {% if disabled %}disabled="disabled"{% endif %} />
        {% if suffix %}
            <span class="add-on">{{suffix}}</span>
        {% endif %}
        {% if prefix or suffix %}
            </div>
        {% endif %}

        </td></tr></table></td></tr>
        {% if corrective_hint %}
            <tr><td><table class="corrective-hint containerpagination-right"><tr><td style="font-size: {{fontsize}}pt;">{{ corrective_hint }}</td></tr></table></td></tr>
        {% endif %}
        </table></div>

        ''')

    @property
    def web_widget(self):

        d = {}
        d['alignment'] = alignment_converter(self._alignment, 'container')
        d['fontsize'] = fontsize_converter(self._fontSize)
        d['width'] = self._instructionWidth
        d['height'] = self._instructionHeight
        d['instruction'] = self._instruction
        d['name'] = self.name
        d['input'] = self._input
        d['disabled'] = not self.enabled
        d['prefix'] = self._prefix
        d['suffix'] = self._suffix
        if self.corrective_hints:
            d['corrective_hint'] = self.corrective_hints[0]
        return self._template.render(d)

    @property
    def can_display_corrective_hints_in_line(self):
        return True

    def validate_data(self):
        super(TextEntryElement, self).validate_data()

        if self._forceInput and self._shouldBeShown and self._input == '':
            return False

        return True

    def set_data(self, d):
        '''
        .. todo:: No data can be set when using qt interface (compare web interface functionality). Is this a problem?
        .. update (20.02.2019) removed qt depencies
        '''
        if self.enabled:
            super(TextEntryElement, self).set_data(d)


class TextAreaElement(TextEntryElement):
    def __init__(self, instruction='', x_size=300, y_size=150, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, **kwargs):
        '''
        **TextAreaElement** returns a multiline text edit with an instruction on top.

        :param str name: Name of TextAreaElement and stored input variable.
        :param str instruction: Instruction to be displayed above multiline edit field (can contain html commands).
        :param int instruction_width: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instruction_height: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param int x_size: Horizontal size for visible text edit field in pixels.
        :param int y_size: Vertical size for visible text edit field in pixels.
        :param str alignment: Alignment of TextAreaElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in TextAreaElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''
        super(TextAreaElement, self).__init__(instruction, no_input_corrective_hint=no_input_corrective_hint, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

        self._xSize = x_size
        self._ySize = y_size

    @property
    def web_widget(self):

        widget = '<div class="text-area-element"><table class="%s" style="font-size: %spt;">' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize))

        widget = widget + '<tr><td class="itempagination-left" style="padding-bottom: 10px;">%s</td></tr>' % (self._instruction)

        widget = widget + '<tr><td class="%s"><textarea class="text-input pagination-left" style="font-size: %spt; height: %spx; width: %spx;" name="%s" %s>%s</textarea></td></tr>' % (alignment_converter(self._alignment), fontsize_converter(self._fontSize), self._ySize, self._xSize, self.name, "" if self.enabled else " disabled=\"disabled\"", self._input)

        if self.corrective_hints:
            widget = widget + '<tr><td class="corrective-hint %s" style="font-size: %spt;">%s</td></tr>' % (alignment_converter(self._alignment, 'both'), fontsize_converter(self._fontSize) - 1, self.corrective_hints[0])

        widget = widget + '</table></div>'

        return widget

    @property
    def css_code(self):
        return [(99, ".TextareaElement { resize: none; }")]

    def set_data(self, d):
        if self.enabled:
            super(TextAreaElement, self).set_data(d)


class RegEntryElement(TextEntryElement):
    def __init__(self, instruction='', reg_ex='.*', no_input_corrective_hint=None, match_hint=None, instruction_width=None, instruction_height=None, **kwargs):
        '''
        **RegEntryElement*** displays a line edit, which only accepts Patterns that mach a predefined regular expression. Instruction is shown
        on the left side of the line edit field.

        :param str name: Name of TextAreaElement and stored input variable.
        :param str instruction: Instruction to be displayed above multiline edit field (can contain html commands).
        :param str reg_ex: Regular expression to match with user input.
        :param str alignment: Alignment of TextAreaElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in TextAreaElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        super(RegEntryElement, self).__init__(instruction, no_input_corrective_hint=no_input_corrective_hint, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

        self._regEx = reg_ex
        self._matchHint = match_hint

    def validate_data(self):
        super(RegEntryElement, self).validate_data()

        if not self._shouldBeShown:
            return True

        if not self._forceInput and self._input == '':
            return True

        if re.match(r'^%s$' % self._regEx, str(self._input)):
            return True

        return False

    @property
    def match_hint(self):
        if self._matchHint is not None:
            return self._matchHint
        if self._question and self._question._experiment\
                and 'corrective_regentry' in self._question._experiment.settings.hints:
            return self._question._experiment.settings.hints['corrective_regentry']
        logger.error("Can't access match_hint for %s " % type(self).__name__)
        return "Can't access match_hint for %s " % type(self).__name__

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        elif re.match(r'^%s$' % self._regEx, self._input):
            return []
        elif self._input == '' and not self._forceInput:
            return []
        elif self._input == '' and self._forceInput:
            return [self.no_input_hint]
        else:
            return [self.match_hint]


class NumberEntryElement(RegEntryElement):
    def __init__(self, instruction='', decimals=0, min=None, max=None, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, match_hint=None, **kwargs):
        '''
        **NumberEntryElement*** displays a line edit, which only accepts numerical input. Instruction is shown
        on the left side of the line edit field.

        :param str name: Name of NumberEntryElement and stored input variable.
        :param str instruction: Instruction to be displayed above multiline edit field (can contain html commands).
        :param int decimals: Accepted number of decimals (0 as standard).
        :param float min: Minimum accepted entry value.
        :param float max: Maximum accepted entry value.
        :param int spacing: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of NumberEntryElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in NumberEntryElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.

        '''
        super(NumberEntryElement, self).__init__(instruction, no_input_corrective_hint=no_input_corrective_hint, instruction_width=instruction_width, instruction_height=instruction_height, match_hint=match_hint, **kwargs)

        self._validator = None
        self._decimals = decimals
        self._min = min
        self._max = max

        self._template = jinja2.Template('''
        <div class="text-entry-element"><table class="{{ alignment }}" style="font-size: {{ fontsize }}pt";>
        <tr><td valign="bottom"><table class="{{ alignment }}"><tr><td style="padding-right: 5px;{% if width %}width:{{width}}px;{% endif %}{% if height %}width:{{height}}px;{% endif %}">{{ instruction }}</td>
        <td valign="bottom">
        {% if prefix or suffix %}
            <div class="{% if prefix %}input-prepend {% endif %}{% if suffix %}input-append {% endif %}" style="margin-bottom: 0px;">
        {% endif %}
        {% if prefix %}
            <span class="add-on">{{prefix}}</span>
        {% endif %}
        <input class="text-input" type="number" style="font-size: {{ fontsize }}pt; margin-bottom: 0px;" name="{{ name }}" value="{{ input }}" {% if disabled %}disabled="disabled"{% endif %} {% if max is defined %}max={{ max }}{% endif %} {% if min is defined %}min={{ min }}{% endif %} {% if step %}step={{ step }}{% endif %} />
        {% if suffix %}
            <span class="add-on">{{suffix}}</span>
        {% endif %}
        {% if prefix or suffix %}
            </div>
        {% endif %}

        </td></tr></table></td></tr>
        {% if corrective_hint %}
            <tr><td><table class="corrective-hint containerpagination-right"><tr><td style="font-size: {{fontsize}}pt;">{{ corrective_hint }}</td></tr></table></td></tr>
        {% endif %}
        </table></div>

        ''')

    @property
    def web_widget(self):

        d = {}
        d['alignment'] = alignment_converter(self._alignment, 'container')
        d['fontsize'] = fontsize_converter(self._fontSize)
        d['width'] = self._instructionWidth
        d['height'] = self._instructionHeight
        d['instruction'] = self._instruction
        d['name'] = self.name
        d['input'] = self._input
        d['disabled'] = not self.enabled
        d['prefix'] = self._prefix
        d['suffix'] = self._suffix
        d['step'] = None if self._decimals == 0 else '0.' + ''.join('0' for i in range(1, self._decimals)) + '1'
        d['min'] = self._min
        d['max'] = self._max
        if self.corrective_hints:
            d['corrective_hint'] = self.corrective_hints[0]
        return self._template.render(d)

    def validate_data(self):
        '''
        '''
        super(NumberEntryElement, self).validate_data()

        if not self._shouldBeShown:
            return True

        if not self._forceInput and self._input == '':
            return True

        try:
            f = float(self._input)
        except Exception:
            return False

        if self._min is not None:
            if not self._min <= f:
                return False

        if self._max is not None:
            if not f <= self._max:
                return False

        re_str = r"^[+-]?\d+$" if self._decimals == 0 else r"^[+-]?(\d*[.,]\d{1,%s}|\d+)$" % self._decimals
        if re.match(re_str, str(self._input)):
            return True

        return False

    @property
    def data(self):
        if 0 < self._decimals:
            try:
                tempInput = float(self._input)
            except Exception:
                tempInput = ''
        else:
            try:
                tempInput = int(self._input)
            except Exception:
                tempInput = ''

        return({self.name: tempInput} if self.validate_data() and tempInput != '' else {self.name: ''})

    def set_data(self, d):

        if self.enabled:
            val = d.get(self.name, '')
            if not isinstance(val, str):
                val = str(val)
            val = val.replace(',', '.')
            super(NumberEntryElement, self).set_data({self.name: val})

    @property
    def match_hint(self):
        if self._matchHint is not None:
            return self._matchHint

        if self._question and self._question._experiment\
                and 'corrective_numberentry' in self._question._experiment.settings.hints:
            return self._question._experiment.settings.hints['corrective_numberentry']
        logger.error("Can't access match_hint for %s " % type(self).__name__)
        return "Can't access match_hint for %s " % type(self).__name__

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []

        elif self._input == '' and not self._forceInput:
            return []

        elif self._forceInput and self._input == '':
            return [self.no_input_hint]
        else:
            re_str = r"^[+-]?\d+$" if self._decimals == 0 else r"^[+-]?(\d*[.,]\d{1,%s}|\d+)$" % self._decimals
            if not re.match(re_str, str(self._input)) \
                    or (self._min is not None and not self._min <= float(self._input)) \
                    or (self._max is not None and not float(self._input) <= self._max):

                hint = self.match_hint

                if 0 < self._decimals:
                    hint = hint + u' (Bis zu %s Nachkommastellen' % (self._decimals)
                else:
                    hint = hint + u' (Keine Nachkommastellen'

                if self._min is not None and self._max is not None:
                    hint = hint + ', Min = %s, Max = %s)' % (self._min, self._max)
                elif self._min is not None:
                    hint = hint + ', Min = %s)' % self._min
                elif self._max is not None:
                    hint = hint + ', Max = %s)' % self._max
                else:
                    hint = hint + ')'
                return [hint]

            return []


class PasswordElement(TextEntryElement):
    def __init__(self, instruction='', password='', force_input=True, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, wrong_password_hint=None, **kwargs):
        '''
        **PasswordElement*** desplays a single line text edit for entering a password (input is not visible) with an instruction text on its' left.

        :param str name: Name of PasswordElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param str password: Password to be matched against user input.
        :param int spacing: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of PasswordElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in PasswordElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (True as standard or False).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        :param str wrong_password_hint: Hint to be displayed if user input does not equal password.

        .. caution:: If force_input is set to false, any input will be accepted, but still validated against correct password.
        '''
        super(PasswordElement, self).__init__(instruction, no_input_corrective_hint=no_input_corrective_hint, force_input=force_input, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

        self._password = password
        self.wrong_password_hint_user = wrong_password_hint

    @property
    def web_widget(self):

        widget = '<div class="text-entry-element"><table class="%s" style="font-size: %spt;">' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize))

        widget = widget + '<tr><td valign="bottom"><table class="%s"><tr><td %s>%s</td>' % (alignment_converter(self._alignment, 'container'), 'style="width: %spx;"' % self._instructionWidth if self._instructionWidth is not None else "", self._instruction)

        widget = widget + '<td valign="bottom"><input class="text-input" type="password" style="font-size: %spt; margin-bottom: 0px; margin-left: 5px;" name="%s" value="%s" %s /></td></tr></table></td></tr>' % (fontsize_converter(self._fontSize), self.name, self._input, "" if self.enabled else 'disabled="disabled"')

        if self.corrective_hints:
            widget = widget + '<tr><td><table class="corrective-hint containerpagination-right"><tr><td style="font-size: %spt;">%s</td></tr></table></td></tr>' % (fontsize_converter(self._fontSize), self.corrective_hints[0])

        widget = widget + '</table></div>'

        return widget

    def validate_data(self):
        super(PasswordElement, self).validate_data()

        if not self._forceInput or not self._shouldBeShown:
            return True

        return self._input == self._password

    @property
    def wrong_password_hint(self):
        if self.wrong_password_hint_user is not None:
            return self.wrong_password_hint_user
        elif self._question and self._question._experiment\
                and 'corrective_password' in self._question._experiment.settings.hints:
            return self._question._experiment.settings.hints['corrective_password']
        logger.error("Can't access wrong_password_hint for %s " % type(self).__name__)
        return "Can't access wrong_password_hint for %s " % type(self).__name__

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and self._input == '' and self._password != '':
            return [self.no_input_hint]

        if self._password != self._input:
            return [self.wrong_password_hint]
        else:
            return []

    @property
    def data(self):
        return {}


class LikertMatrix(InputElement, WebElementInterface):
    def __init__(self, instruction='', levels=7, items=4, top_scale_labels=None,
                 bottom_scale_labels=None, item_labels=None, item_label_width=None, spacing=30,
                 transpose=False, no_input_corrective_hint=None, table_striped=False, shuffle=False,
                 instruction_width=None, instruction_height=None, useShortLabels=False, **kwargs):
        '''
        **LikertMatrix** displays a matrix of multiple likert items with adjustable scale levels per item.
        Instruction is shown above element.

        :param str name: Name of LikertMatrix and stored input variable.
        :param str instruction: Instruction to be displayed above likert matrix (can contain html commands).
        :param int levels: Number of scale levels.
        :param int items: Number of items in matrix (rows or columns if transpose = True).
        :param list top_scale_labels: Labels for each scale level on top of the Matrix.
        :param list bottom_scale_labels: Labels for each scale level under the Matrix.
        :param list item_labels: Labels for each item on both sides of the scale.
        :param int spacing: Sets column width or row height (if transpose set to True) in likert matrix, can be used to ensure symmetric layout.
        :param bool transpose: If set to True matrix is layouted vertically instead of horizontally.
        :param str alignment: Alignment of LikertMatrix in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in LikertMatrix ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        super(LikertMatrix, self).__init__(no_input_corrective_hint=no_input_corrective_hint, **kwargs)

        if spacing < 30:
            raise ValueError('Spacing must be greater or equal than 30!')

        self._instruction = instruction
        self._instructionWidth = instruction_width
        self._instructionHeight = instruction_height
        self._levels = levels
        self._items = items
        self._itemLabelWidth = item_label_width
        self._spacing = spacing
        self._tableStriped = table_striped
        self._transpose = transpose
        self._useShortLabels = useShortLabels

        self._defaultSet = False

        self._permutation = list(range(items))
        if shuffle:
            random.shuffle(self._permutation)

        if top_scale_labels is not None and not len(top_scale_labels) == self._levels:
            raise ValueError(u"Es mussen keine oder %s OBERE (bei Transpose LINKE) Skalenlabels ubergeben werden." % self._levels)
        self._topScaleLabels = top_scale_labels

        if bottom_scale_labels is not None and not len(bottom_scale_labels) == self._levels:
            raise ValueError(u"Es mussen keine oder %s UNTERE (bei Transpose RECHTE) Skalenlabels ubergeben werden." % self._levels)
        self._bottomScaleLabels = bottom_scale_labels

        if item_labels is not None and not len(item_labels) == (2 * self._items):
            raise ValueError(u"Es mussen keine oder %s Itemlabels ubergeben werden." % (2 * self._items))
        self._itemLabels = item_labels

        if settings.debugmode and settings.debug.defaultValues:
            self._input = [str(int(self._input) - 1) for i in range(self._items)]
        elif not self._input == '':
            self._input = [str(int(self._input) - 1) for i in range(self._items)]
            self._defaultSet = True
        else:
            self._input = ['-1' for i in range(self._items)]

    @property
    def can_display_corrective_hints_in_line(self):
        return True

    @property
    def data(self):
        lmData = {}
        for i in range(self._items):
            label = self.name + '_' + str(i + 1)
            if self._useShortLabels:
                short_labels = self._short_labels()
                label += '_' + short_labels[i]
            lmData.update({label: None if int(self._input[i]) + 1 == 0 else int(self._input[i]) + 1})
        lmData[self.name + '_permutation'] = [i + 1 for i in self._permutation]
        return lmData

    def _short_labels(self):
        L = 6
        rv = []
        for i in range(self._items):
            label = self._itemLabels[2 * i]
            if label != '':
                label = label.replace('.', '')
                words = label.split()
                num = int(round((old_div(L, len(words))) + 0.5))
                sl = ''
                for w in words:
                    sl = sl + w[:num]
                rv.append(sl[:L])
            else:
                rv.append('')
        return rv

    @property
    def web_widget(self):

        widget = '<div class="likert-matrix"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize), 'style="width: %spx;"' % self._instructionWidth if self._instructionWidth is not None else "", self._instruction)  # Extra Table for instruction

        widget = widget + '<table class="%s %s table" style="width: auto; clear: both; font-size: %spt; margin-bottom: 10px;">' % (alignment_converter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsize_converter(self._fontSize))  # Beginning Table

        if not self._transpose:
            if self._topScaleLabels:
                widget = widget + '<thead><tr><th></th>'  # Beginning row for top scalelabels, adding 1 column for left item_labels
                for label in self._topScaleLabels:
                    widget = widget + '<th class="pagination-centered containerpagination-centered" style="text-align:center;width: %spx; vertical-align: bottom;">%s</th>' % (self._spacing, label)  # Adding top Scalelabels

                widget = widget + "<th></th></tr></thead>"  # adding 1 Column for right Itemlabels, ending Row for top Scalelabels

            widget = widget + '<tbody>'
            for i in self._permutation:
                widget = widget + '<tr>'  # Beginning new row for item
                if self._itemLabels:
                    widget = widget + '<td style="text-align:right; vertical-align: middle;">%s</td>' % self._itemLabels[i * 2]  # Adding left itemlabel
                else:
                    widget = widget + '<td></td>'  # Placeholder if no item_labels set

                for j in range(self._levels):  # Adding Radiobuttons for each level
                    widget = widget + '<td style="text-align:center; vertical-align: middle; margin: auto auto;"><input type="radio" style="margin: 4px 4px 4px 4px;" name="%s" value="%s" %s %s /></td>' % (self.name + '_' + str(i), j, " checked=\"checked\"" if self._input[i] == str(j) else "", "" if self.enabled else " disabled=\"disabled\"")

                if self._itemLabels:
                    widget = widget + '<td style="text-align:left;vertical-align: middle;">%s</td>' % self._itemLabels[(i + 1) * 2 - 1]  # Adding right itemlabel
                else:
                    widget = widget + '<td></td>'  # Placeholder if no item_labels set

                widget = widget + '</tr>'  # Closing row for item
            widget = widget + '</tbody>'

            if self._bottomScaleLabels:
                widget = widget + '<tfoot><tr><th></th>'  # Beginning row for bottom scalelabels, adding 1 column for left item_labels
                for label in self._bottomScaleLabels:
                    widget = widget + '<th class="pagination-centered containerpagination-centered" style="text-align:center;width: %spx; vertical-align: top;">%s</th>' % (self._spacing, label)  # Adding bottom Scalelabels

                widget = widget + "<th></th></tr></tfoot>"  # adding 1 Column for right Itemlabels, ending Row for bottom Scalelabels

            widget = widget + "</table>"  # Closing table for LikertMatrix

        else:  # If transposed is set to True
            if self._itemLabels:
                widget = widget + '<tr><td></td>'  # Beginning row for top (left without transpose) item_labels, adding 1 column for left (top without transpose) scalelabels
                for i in range(old_div(len(self._itemLabels), 2)):
                    widget = widget + '<td class="pagination-centered containerpagination-centered" style="text-align:center; vertical-align: bottom;">%s</td>' % self._itemLabels[i * 2]  # Adding top item_labels

                widget = widget + "<td></td></tr>"  # adding 1 Column for right scalelabels, ending Row for top item_labels

            for i in range(self._levels):
                widget = widget + '<tr style="height: %spx;">' % self._spacing  # Beginning new row for level
                if self._topScaleLabels:
                    widget = widget + '<td class="pagination-right" style="vertical-align: middle;">%s</td>' % self._topScaleLabels[i]  # Adding left scalelabel
                else:
                    widget = widget + '<td></td>'  # Placeholder if no scalelabels set

                for j in range(self._items):  # Adding Radiobuttons for each item
                    widget = widget + '<td class="pagination-centered" style="text-align:center; vertical-align: middle; margin: auto auto;"><input type=\"radio\" style="margin: 4px 4px 4px 4px;" name=\"%s\" value=\"%s\"%s%s /></td>' % (self.name + '_' + str(j), i, " checked=\"checked\"" if self._input[j] == str(i) else "", "" if self.enabled else " disabled=\"disabled\"")

                if self._bottomScaleLabels:
                    widget = widget + '<td class="pagination-left" style="vertical-align: middle;">%s</td>' % self._bottomScaleLabels[i]  # Adding right scalelabel
                else:
                    widget = widget + '<td></td>'  # Placeholder if no scalelabels set

                widget = widget + '</tr>'  # Closing row for level

            if self._itemLabels:
                widget = widget + '<tr><td></td>'  # Beginning row for bottom (right without transpose) item_labels, adding 1 column for left (top without transpose) scalelabels
                for i in range(old_div(len(self._itemLabels), 2)):
                    widget = widget + '<td class="pagination-centered containerpagination-centered" style="text-align:center; vertical-align: top;">%s</td>' % self._itemLabels[(i + 1) * 2 - 1]  # Adding bottom item_labels

                widget = widget + "<td></td></tr>"  # adding 1 Column for right scalelabels, ending Row for bottom item_labels

            widget = widget + "</table>"  # Closing table for LikertMatrix

        if self.corrective_hints:

            widget = widget + '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize) - 1, self.corrective_hints[0])

        widget = widget + "</div>"

        return widget

    def validate_data(self):
        super(LikertMatrix, self).validate_data()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            for i in range(self._items):
                value = int(self._input[i])
                ret = ret and 0 <= value <= self._levels
            return ret
        except Exception:
            return False

    def set_data(self, d):
        if self.enabled:
            for i in range(self._items):
                self._input[i] = d.get(self.name + '_' + str(i), '-1')

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and reduce(lambda b, val: b or val == '-1', self._input, False):
            return [self.no_input_hint]
        else:
            return super(InputElement, self).corrective_hints


class LikertElement(LikertMatrix):
    def __init__(self, instruction='', levels=7, top_scale_labels=None, bottom_scale_labels=None, item_labels=None, item_label_width=None, spacing=30, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, transpose=False, **kwargs):
        '''
        **LikertElement** returns a single likert item with n scale levels and an instruction shown above the element.

        :param str name: Name of LikertElement and stored input variable.
        :param str instruction: Instruction to be displayed above likert matrix (can contain html commands).
        :param int levels: Number of scale levels.
        :param list topscalelabels: Labels for each scale level on top of the Item.
        :param list bottomscalelabels: Labels for each scale level under the Item.
        :param list itemlabels: Labels on both sides of the scale.
        :param int spacing: Sets column width or row height (if transpose set to True) in LikertElement, can be used to ensure symmetric layout.
        :param bool transpose: If True item is layouted vertically instead of horizontally.
        :param str alignment: Alignment of LikertElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in LikertElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''
        super(LikertElement, self).__init__(instruction=instruction, items=1, levels=levels, top_scale_labels=top_scale_labels, bottom_scale_labels=bottom_scale_labels, item_labels=item_labels, item_label_width=item_label_width, spacing=spacing, no_input_corrective_hint=no_input_corrective_hint, table_striped=False, transpose=transpose, shuffle=False, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

    @property
    def data(self):
        lmData = {}
        lmData.update({self.name: None if int(self._input[0]) + 1 == 0 else int(self._input[0]) + 1})
        return lmData


class SingleChoiceElement(LikertElement):
    def __init__(self, instruction='', item_labels=[], item_label_width=None, item_label_height=None, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, shuffle=False, table_striped=False, **kwargs):
        '''
        **SingleChoiceElement** returns a vertically layouted item with adjustable choice alternatives (comparable to levels of likert scale),
        from which only one can be selected.

        :param str name: Name of SingleChoiceElement and stored input variable.
        :param str instruction: Instruction to be displayed above SingleChoiceElement (can contain html commands).
        :param int levels: Number of choice alternatives.
        :param list labels: Labels for each choice alternative on the right side of the scale.
        :param int spacing: Sets row height in SingleChoiceElement, can be used to ensure symmetric layout.
        :param str alignment: Alignment of SingleChoiceElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in SingleChoiceElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        kwargs.pop('transpose', None)  # Stellt sicher, dass keine ungültigen Argumente verwendet werden
        kwargs.pop('items', None)  # Stellt sicher, dass keine ungültigen Argumente verwendet werden

        if len(item_labels) == 0:
            raise ValueError(u"Es müssen Itemlabels übergeben werden.")

        super(SingleChoiceElement, self).__init__(instruction=instruction, no_input_corrective_hint=no_input_corrective_hint, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

        self._permutation = list(range(len(item_labels)))
        if shuffle:
            random.shuffle(self._permutation)

        self._itemLabelWidth = item_label_width
        self._itemLabelHeight = item_label_height
        self._tableStriped = table_striped
        self._items = len(item_labels)
        self._itemLabels = item_labels
        self._suffle = shuffle

        if settings.debugmode and settings.debug.defaultValues:
            self._input = str(int(self._input[0]))
        elif not self._input == '':
            self._input = str(int(self._input[0]))
            self._defaultSet = True
        else:
            self._input = '-1'

    @property
    def web_widget(self):

        widget = '<div class="single-choice-element"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize), 'style="width: %spx;"' % self._instructionWidth if self._instructionWidth is not None else "", self._instruction)  # Extra Table for instruction

        widget = widget + '<table class="%s %s table" style="width: auto; clear: both; font-size: %spt; margin-bottom: 10px;">' % (alignment_converter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsize_converter(self._fontSize))  # Beginning Table

        for i in range(self._items):  # Adding Radiobuttons for each sclae level in each likert item

            widget = widget + '<tr><td class="pagination-centered" style="vertical-align: middle; margin: auto auto;"><input type=\"radio\" style="margin: 4px 4px 4px 4px;" name=\"%s\" value=\"%s\"%s%s /></td>' % (self.name, self._permutation[i], " checked=\"checked\"" if self._input == str(self._permutation[i]) else "", "" if self.enabled else " disabled=\"disabled\"")

            widget = widget + '<td class="pagination-left" style="vertical-align: middle;" %s>%s</td></tr>' % ('width: ' + str(self._itemLabelWidth) + 'px;' if self._itemLabelWidth else '', self._itemLabels[self._permutation[i]])  # Adding item label

        widget = widget + "</table>"  # Closing table for SingleChoiceElement

        if self.corrective_hints:
            widget = widget + '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize), self.corrective_hints[0])

        widget = widget + '</div>'

        return widget

    def set_data(self, d):
        if self.enabled:
            self._input = d.get(self.name, '-1')

    @property
    def data(self):
        d = {self.name: None if int(self._input) + 1 == 0 else int(self._input) + 1}
        if self._suffle:
            d[self.name + '_permutation'] = [i + 1 for i in self._permutation]
        return d

    def validate_data(self):
        super(SingleChoiceElement, self).validate_data()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            value = int(self._input)
            ret = ret and 0 <= value <= self._levels
            return ret
        except Exception:
            return False

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and self._input == '-1':
            return [self.no_input_hint]
        else:
            return super(InputElement, self).corrective_hints


class MultipleChoiceElement(LikertElement):
    def __init__(self, instruction='', item_labels=[], min_select=None, max_select=None, select_hint=None, item_label_width=None, item_label_height=None, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, shuffle=False, table_striped=False, **kwargs):
        '''
        **SingleChoiceElement** returns a vertically layouted item with adjustable choice alternatives (comparable to levels of likert scale)
        as checkboxes, from which one or more can be selected.

        :param str name: Name of MultipleChoiceElement and stored input variable.
        :param str instruction: Instruction to be displayed above MultipleChoiceElement (can contain html commands).
        :param int levels: Number of choice alternatives.
        :param list labels: Labels for each choice alternative on the right side of the scale.
        :param int spacing: Sets row height in MultipleChoiceElement, can be used to ensure symmetric layout.
        :param str alignment: Alignment of MultipleChoiceElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in MultipleChoiceElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        kwargs.pop('transpose', None)  # Stellt sicher, dass keine ungültigen Argumente verwendet werden
        kwargs.pop('items', None)  # Stellt sicher, dass keine ungültigen Argumente verwendet werden

        default = kwargs.pop('default', None)
        debug_string = kwargs.pop('debug_string', None)

        if len(item_labels) == 0:
            raise ValueError(u"Es müssen Itemlabels übergeben werden.")

        super(MultipleChoiceElement, self).__init__(instruction=instruction, no_input_corrective_hint=no_input_corrective_hint, instruction_width=instruction_width, instruction_height=instruction_height, **kwargs)

        self._permutation = list(range(len(item_labels)))
        if shuffle:
            random.shuffle(self._permutation)

        self._itemLabelWidth = item_label_width
        self._itemLabelHeight = item_label_height
        self._tableStriped = table_striped
        self._items = len(item_labels)

        if min_select and min_select > self._items:
            raise ValueError('min_select must be smaller than number of items')

        if max_select and max_select < 2:
            raise ValueError('max_select must be set to 2 or higher')

        self._minSelect = min_select
        self._maxSelect = max_select

        if select_hint:
            self._select_hint = select_hint
        else:
            if min_select and not max_select:
                self._select_hint = u"Bitte wählen Sie mindestens %i Optionen aus" % self._minSelect
            elif max_select and not min_select:
                self._select_hint = u"Bitte wählen Sie höchstens %i Optionen aus" % self._maxSelect
            elif max_select and min_select:
                self._select_hint = u"Bitte wählen Sie mindestens %i und höchstens %i Optionen aus" % (self._minSelect, self._maxSelect)

        if self._minSelect:
            self._noInputCorrectiveHint = self._select_hint

        self._itemLabels = item_labels
        self._suffle = shuffle

        # default values and debug values have to be implemented with the following workaround resulting from deducing LikertItem

        self._input = ['0' for i in range(len(self._itemLabels))]

        if settings.debugmode and settings.debug.defaultValues:
            if not debug_string:
                self._input = settings.debug.get(self.__class__.__name__)  # getting default value (True or False)
            else:
                self._input = settings._config_parser.get('debug', debug_string)

            if self._input is True:
                self._input = ['1' for i in range(len(self._itemLabels))]
            else:
                self._input = ['0' for i in range(len(self._itemLabels))]

        if default is not None:
            self._input = default

            if not len(self._input) == len(self._itemLabels):
                raise ValueError('Wrong default data! Default value must be set to a list of %s values containing either "0" or "1"!' % (len(self._itemLabels)))

    @property
    def web_widget(self):

        widget = '<div class="multiple-choice-element"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize), 'style="width: %spx;"' % self._instructionWidth if self._instructionWidth is not None else "", self._instruction)  # Extra Table for instruction

        widget = widget + '<table class="%s %s" style="clear: both; font-size: %spt; line-height: normal; margin-bottom: 10px;">' % (alignment_converter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsize_converter(self._fontSize))  # Beginning Table

        for i in range(self._items):
            widget = widget + '<tr style="height: %spx;"><td class="pagination-centered" style="vertical-align: middle; margin: auto auto;"><input type="checkbox" style="vertical-align: middle; margin: 4px 4px 4px 4px;" name="%s" value="%s" %s %s /></td>' % (self._spacing, self.name + '_' + str(self._permutation[i]), 1, " checked=\"checked\"" if self._input[self._permutation[i]] == '1' else "", "" if self.enabled else " disabled=\"disabled\"")
            widget = widget + '<td class="pagination-left" style="vertical-align: middle;">%s</td></tr>' % self._itemLabels[self._permutation[i]]

        widget = widget + '</table>'

        if self.corrective_hints:
            widget = widget + '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize), self.corrective_hints[0])

        widget = widget + '</div>'

        return widget

    @property
    def data(self):
        mcData = {}
        for i in range(self._items):
            mcData.update({self.name + '_' + str(i + 1): int(self._input[i])})
        if self._suffle:
            mcData[self.name + '_permutation'] = [i + 1 for i in self._permutation]
        return mcData

    def set_data(self, d):
        if self.enabled:
            for i in range(self._items):
                self._input[i] = d.get(self.name + '_' + str(i), '0')

    def validate_data(self):
        if not self._forceInput or not self._shouldBeShown:
            return True

        if not self._minSelect and not self._maxSelect:
            for item in self._input:
                if item == '1':
                    return True
        else:
            count = 0
            for item in self._input:
                if item == '1':
                    count += 1

            if self._minSelect and count < self._minSelect:
                return False
            if self._maxSelect and count > self._maxSelect:
                return False

            return True

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and not reduce(lambda b, val: b or val == '1', self._input, False):
            return [self.no_input_hint]

        if self._minSelect or self._maxSelect:
            hints = []
            count = 0
            for item in self._input:
                if item == '1':
                    count += 1

            if self._minSelect and count < self._minSelect:
                hints.append(self._select_hint)
            elif self._maxSelect and count > self._maxSelect:
                hints.append(self._select_hint)

            return hints

        return super(InputElement, self).corrective_hints


class LikertListElement(InputElement, WebElementInterface):
    def __init__(self, instruction='', levels=7, top_scale_labels=None, bottom_scale_labels=None,
                 item_labels=[], item_label_height=None, item_label_width=None, itemLabelAlignment='left',
                 table_striped=False, spacing=30, shuffle=False, instruction_width=None,
                 instruction_height=None, useShortLabels=False, **kwargs):
        '''
        **LikertListElement** displays a likert item with images as labels.
        Instruction is shown above element.

        :param str name: Name of WebLikertImageElement and stored input variable.
        :param str instruction: Instruction to be displayed above likert matrix (can contain html commands).
        :param int levels: Number of scale levels..
        :param int spacing: Sets column width between radio buttons.
        :param str alignment: Alignment of WebLikertImageElement in widget container ('left' as default, 'center', 'right').
        :param str/int font: Fontsize used in WebLikertImageElement ('normal' as default, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as default or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        super(LikertListElement, self).__init__(**kwargs)

        self._instruction = instruction
        self._instructionWidth = instruction_width
        self._instructionHeight = instruction_height
        self._levels = levels
        self._topScaleLabels = top_scale_labels
        self._bottomScaleLabels = bottom_scale_labels
        self._itemLabels = item_labels
        self._itemLabelHeight = item_label_height
        self._itemLabelWidth = item_label_width
        self._itemLabelAlign = itemLabelAlignment
        self._tableStriped = table_striped
        self._spacing = spacing
        self._defaultSet = False
        self._useShortLabels = useShortLabels

        if spacing < 30:
            raise ValueError(u'Spacing must be greater or equal than 30!')

        if top_scale_labels is not None and not len(top_scale_labels) == self._levels:
            raise ValueError(u"Es müssen keine oder %s OBERE Skalenlabels übergeben werden." % self._levels)

        if bottom_scale_labels is not None and not len(bottom_scale_labels) == self._levels:
            raise ValueError(u"Es müssen keine oder %s UNTERE Skalenlabels übergeben werden." % self._levels)

        self._permutation = list(range(len(item_labels)))
        if shuffle:
            random.shuffle(self._permutation)

        if settings.debugmode and settings.debug.defaultValues:
            self._input = [str(int(self._input) - 1) for i in item_labels]
        elif not self._input == '':
            self._input = [str(int(self._input) - 1) for i in item_labels]
            self._defaultSet = True
        else:
            self._input = ['-1' for i in item_labels]

        self._template = jinja2.Template('''
            <div class="" style="font-size: {{fontsize}}pt; text-align: {{alignment}}">
                {% if instruction %}<p>{{instruction}}</p>{% endif %}
                <table class="{{contalignment}} table {{striped}}" style="width: auto;">
                    {% if topscalelabels %}
                    <thead>
                    <tr>
                        <th></th>
                        {% for topscalelabel in topscalelabels %}
                            <th style="text-align:center;">{{topscalelabel}}</th>
                        {% endfor %}
                    </tr>
                    </thead>
                    {% endif %}
                    {% if bottomscalelabels %}
                    <tfoot>
                    <tr>
                        <th></th>
                        {% for bottomscalelabel in bottomscalelabels %}
                            <th style="text-align:center;">{{bottomscalelabel}}</th>
                        {% endfor %}
                    </tr>
                    </tfoot>
                    {% endif %}
                    <tbody>
                    {% for i in permutation %}
                        <tr>
                        <td style="text-align: {{itemlabel_align}};{% if itemlabel_width%}width: {{itemlabel_width}}px;{% endif %}">{{itemlabels[i]}}</td>
                        {% for j in range(levels) %}
                            <td style="width:{{spacing}}pt;vertical-align: middle; text-align:center;"><input type="radio" style="margin: 4px 4px 4px 4px;" name={{name}}_{{i}} value="{{j}}"{% if j == values[i] %} checked="checked"{% endif %}{% if not enabled %} disabled="disabled"{% endif %} /></td>
                        {% endfor %}
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% for hint in hints%}
                    <p style="color: red;">{{hint}}</p>
                {% endfor %}

            </div>
            ''')

    @property
    def can_display_corrective_hints_in_line(self):
        return True

    def _short_labels(self):
        L = 6
        rv = []
        for label in self._itemLabels:
            if label != '':
                label = label.replace('.', '')
                words = label.split()
                num = int(round((old_div(L, len(words))) + 0.5))
                sl = ''
                for w in words:
                    sl = sl + w[:num]
                rv.append(sl[:L])
            else:
                rv.append('')
        return rv

    @property
    def data(self):
        d = {}
        d[self._name + '_permutation'] = [i + 1 for i in self._permutation]
        short_labels = self._short_labels()
        for i in range(len(self._itemLabels)):
            label = self.name + '_' + str(i + 1)
            if self._useShortLabels:
                label += '_' + short_labels[i]
            d[label] = int(self._input[i]) + 1
            if d[label] == 0:
                d[label] = None
        return d

    def set_data(self, d):
        if self._enabled:
            for i in range(len(self._itemLabels)):
                self._input[i] = d.get(self.name + '_' + str(i), '-1')

    @property
    def web_widget(self):
        d = {}
        d['fontsize'] = fontsize_converter(self._fontSize)
        d['contalignment'] = alignment_converter(self._alignment, 'container')
        d['alignment'] = self._alignment
        d['instruction'] = self._instruction
        d['striped'] = 'table-striped' if self._tableStriped else ''
        d['spacing'] = self._spacing
        d['hints'] = self.corrective_hints
        d['name'] = self.name
        d['enabled'] = self.enabled
        d['levels'] = self._levels
        d['values'] = [int(v) for v in self._input]
        d['permutation'] = self._permutation
        d['topscalelabels'] = self._topScaleLabels
        d['bottomscalelabels'] = self._bottomScaleLabels
        d['itemlabels'] = self._itemLabels
        d['itemlabel_width'] = self._itemLabelWidth
        d['itemlabel_align'] = self._itemLabelAlign

        return self._template.render(d)

    def validate_data(self):
        super(LikertListElement, self).validate_data()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            for v in self._input:
                ret = ret and 0 <= int(v) < self._levels
            return ret
        except Exception:
            return False

    @property
    def corrective_hints(self):
        if not self.show_corrective_hints:
            return []
        if self._forceInput and reduce(lambda b, val: b or val == '-1', self._input, False):
            return [self.no_input_hint]
        else:
            return super(LikertListElement, self).corrective_hints


class ImageElement(Element, WebElementInterface):
    def __init__(self, path=None, url=None, x_size=None, y_size=None, alt=None, maximizable=False, **kwargs):
        super(ImageElement, self).__init__(**kwargs)

        if not path and not url:
            raise ValueError('path or url must be set in image element')

        if path and not os.path.isabs(path):
            path = os.path.join(settings.general.external_files_dir, path)

        self._path = path
        self._url = url

        self._xSize = x_size
        self._ySize = y_size
        self._alt = alt
        self._image_url = None
        self._maximizable = maximizable
        self._min_times = []
        self._max_times = []

    def prepare_web_widget(self):
        if self._image_url is None:
            if self._path:
                self._image_url = self._question._experiment.user_interface_controller.add_static_file(self._path)
            elif self._url:
                self._image_url = self._url

    @property
    def web_widget(self):
        html = '<p class="%s">' % alignment_converter(self._alignment, 'text')

        if self._maximizable:
            html = html + '<a href="#" id="link-%s">' % self.name

        html = html + '<img  src="%s" ' % self._image_url
        if self._alt is not None:
            html = html + 'alt="%s"' % self._alt

        html = html + 'style="'

        if self._xSize is not None:
            html = html + ' width: %spx;' % self._xSize

        if self._ySize is not None:
            html = html + ' height: %spx;' % self._ySize
        html = html + '" />'

        if self._maximizable:
            html = html + '</a><input type="hidden" id="%s" name="%s" value="%s"></input><input type="hidden" id="%s" name="%s" value="%s"></input>' \
                % (self.name + '_max_times', self.name + '_max_times', self._min_times, self.name + '_min_times', self.name + '_min_times', self._max_times)

        return html + '</p>'

    @property
    def css_code(self):
        return [(10,
                 '''
            #overlay-%s {position:absolute;left:0;top:0;min-width:100%%;min-height:100%%;z-index:1 !important;background-color:black;
        ''' % self.name)
                ]

    @property
    def js_code(self):
        template = string.Template('''
         $$(document).ready(function(){
         var maxtimes = $$.parseJSON($$('#${maxtimes}').val());
         var mintimes = $$.parseJSON($$('#${mintimes}').val());
         $$('#${linkid}').click(function(){

          // Add time to max_times
          maxtimes.push(new Date().getTime()/1000);
          $$('#${maxtimes}').val(JSON.stringify(maxtimes));

          // Add overlay
          $$('<div id="${overlayid}" />')
           .hide()
           .appendTo('body')
           .fadeIn('fast');

          // Add image & center
          $$('<img id="${imageid}" class="pop" src="${imgurl}" style="max-width: none;">').appendTo('#${overlayid}');
          var img = $$('#${imageid}');
          //img.css({'max-width': 'auto'});
          var imgTop = Math.max(($$(window).height() - img.height())/2, 0);
          var imgLft = Math.max(($$(window).width() - img.width())/2, 0);
          img
           .hide()
           .css({ position: 'relative', top: imgTop, left: imgLft })
           .fadeIn('fast');

          // Add click functionality to hide everything
          $$('#${overlayid}').click(function(){
           // Add time to min_times
           mintimes.push(new Date().getTime()/1000);
           $$('#${mintimes}').val(JSON.stringify(mintimes));

           $$('#${overlayid},#${imageid}').fadeOut('fast',function(){
             $$(this).remove();
             $$('#${overlayid}').remove();
           });
          });
          $$('#${imageid}').click(function(){
           $$('#${overlayid},#${imageid}').fadeOut('fast',function(){
             $$(this).remove();
             $$('#${overlayid}').remove();
           });
          })
         });
        });
            ''')
        return [(10, template.substitute(linkid='link-' + self.name, overlayid='overlay-' + self.name,
                                         imageid='image-' + self.name, imgurl=self._image_url, maxtimes=self.name + '_max_times',
                                         mintimes=self.name + '_min_times'))]

    @property
    def data(self):
        if self._maximizable:
            return {self.name + '_max_times': self._max_times, self.name + '_min_times': self._min_times}
        return {}

    def set_data(self, d):
        if self.enabled and self._maximizable:
            try:
                self._min_times = json.loads(d.get(self.name + '_min_times', '[]'))
                self._max_times = json.loads(d.get(self.name + '_max_times', '[]'))
            except Exception:
                self._min_times = []
                self._max_times = []


class TableElement(Element, WebElementInterface):
    def __init__(self, elements=[], **kwargs):
        super(TableElement, self).__init__(**kwargs)
        self._elements = elements

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, str):
            raise TypeError
        self._name = name
        for row in range(len(self._elements)):
            for column in range(len(self._elements[row])):
                e = self._elements[row][column]
                if not e.name:
                    e.name = self.name + '_' + e.__class__.__name__ + '_r' + str(row) + '_c' + str(column)

    @property
    def flat_elements(self):
        return [e for l in self._elements for e in l]

    def added_to_page(self, q):
        super(TableElement, self).added_to_page(q)
        for e in self.flat_elements:
            e.added_to_page(q)

    @property
    def data(self):
        d = {}
        for e in self.flat_elements:
            d.update(e.data)
        return d

    def set_data(self, data):
        for e in self.flat_elements:
            e.set_data(data)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        for e in self.flat_elements:
            e.enabled = enabled

    @property
    def can_display_corrective_hints_in_line(self):
        return reduce(lambda b, e: b and e.can_display_corrective_hints_in_line, self.flat_elements, True)

    @property
    def corrective_hints(self):
        return [hint for e in self.flat_elements for hint in e.corrective_hints]

    @property
    def show_corrective_hints(self):
        return self._showCorrectiveHints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        self._showCorrectiveHints = b
        for e in self.flat_elements:
            e.show_corrective_hints = b

    def validate_data(self):
        return reduce(lambda b, e: b and e.validate_data(), self.flat_elements, True)

    @property
    def web_widget(self):
        html = '<table class="%s" style="text-align: center; font-size:%spt">' % (alignment_converter(self._alignment, 'container'), fontsize_converter(self._fontSize))

        for l in self._elements:
            html = html + '<tr>'
            for e in l:
                html = html + '<td>' + e.web_widget if e.should_be_shown else '' + '</td>'
            html = html + '</tr>'
        html = html + '</table>'

        return html

    def prepare_web_widget(self):
        for e in self.flat_elements:
            e.prepare_web_widget()

    @property
    def css_code(self):
        return [code for e in self.flat_elements for code in e.css_code]

    @property
    def css_urls(self):
        return [url for e in self.flat_elements for url in e.css_urls]

    @property
    def js_code(self):
        return [code for e in self.flat_elements for code in e.js_code]

    @property
    def js_urls(self):
        return [url for e in self.flat_elements for url in e.js_urls]


class WebSliderElement(InputElement, WebElementInterface):
    def __init__(self, instruction='', slider_width=200, min=0, max=100, step=1, no_input_corrective_hint=None, instruction_width=None, instruction_height=None, item_labels=None, top_label=None, bottom_label=None, **kwargs):
        '''
        **TextSliderElement*** returns a slider bar.

        :param str name: Name of TextEntryElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param int instruction_width: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instruction_height: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of TextEntryElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Font size used in TextEntryElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool force_input: Sets user input to be mandatory (False as standard or True).
        :param str no_input_corrective_hint: Hint to be displayed if force_input set to True and no user input registered.
        '''

        # TODO: Required image files from jquery-ui are missing! Widget will not be displayed correctly, but works nonetheless.
        super(WebSliderElement, self).__init__(no_input_corrective_hint=no_input_corrective_hint, **kwargs)

        self._instructionWidth = instruction_width
        self._instructionHeight = instruction_height
        self._instruction = instruction
        self._sliderWidth = slider_width
        self._min = min
        self._max = max
        self._step = step

        if item_labels is not None and not len(item_labels) == 2:
            raise ValueError(u"Es müssen keine oder 2 Itemlabels übergeben werden.")
        self._itemLabels = item_labels
        self._topLabel = top_label
        self._bottomLabel = bottom_label

        self._template = jinja2.Template(

            '''
        <div class="web-slider-element">
            <table class="{{ alignment }}" style="font-size: {{ fontsize }}pt;">
            <tr><td valign="bottom">
                <table class="{{ alignment }}">
                <tr><td style="{% if width %}width:{{width}}px;{% endif %}{% if height %}width:{{height}}px;{% endif %}">{{ instruction }}</td></tr>
                <tr><table>
                    <tr><td align="center" colspan="3">{{ toplabel }}</td></tr>
                    <tr><td align="right">{{ l_label }}</td>
                    <td valign="bottom"><div style="width: {{ slider_width }}px; margin-left: 15px; margin-right: 15px; margin-top: 5px; margin-bottom: 5px;" name="{{ name }}" value="{{ input }}" {% if disabled %}disabled="disabled"{% endif %}></div></td>
                    <td align="left">{{ r_label }}</td></tr>
                    <tr><td align="center" colspan="3">{{ bottomlabel }}</td></tr>
                    </table></tr>
                </table></td></tr>

            {% if corrective_hint %}
            <tr><td><table class="corrective-hint containerpagination-right"><tr><td style="font-size: {{fontsize}}pt;">{{ corrective_hint }}</td></tr></table></td></tr>
            {% endif %}

            </table>
        </div>

        <input type="hidden" value="{{ input }}" name="{{ name }}" />

        <script>
        $('div[name={{ name }}]').slider({change: function( event, ui ) {
            $('input[name={{ name }}]').val(ui.value);
        }});

        $('div[name={{ name }}]').slider( "option", "max", {{ max }} );
        $('div[name={{ name }}]').slider( "option", "min", {{ min }} );
        $('div[name={{ name }}]').slider( "option", "step", {{ step }} );

        {% if input != "" %}
            $('div[name={{ name }}]').slider( "option", "value", {{ input }});
        {% endif %}



        </script>

        ''')

    @property
    def web_widget(self):

        d = {}
        d['alignment'] = alignment_converter(self._alignment, 'container')
        d['fontsize'] = fontsize_converter(self._fontSize)
        d['width'] = self._instructionWidth
        d['slider_width'] = self._sliderWidth
        d['height'] = self._instructionHeight
        d['instruction'] = self._instruction
        d['l_label'] = self._itemLabels[0] if self._itemLabels else ''
        d['r_label'] = self._itemLabels[1] if self._itemLabels else ''
        d['toplabel'] = self._topLabel if self._topLabel else ''
        d['bottomlabel'] = self._bottomLabel if self._bottomLabel else ''
        d['name'] = self.name
        d['input'] = self._input
        d['min'] = self._min
        d['max'] = self._max
        d['step'] = self._step
        d['disabled'] = not self.enabled
        if self.corrective_hints:
            d['corrective_hint'] = self.corrective_hints[0]
        return self._template.render(d)

    @property
    def can_display_corrective_hints_in_line(self):
        return True

    def validate_data(self):
        super(WebSliderElement, self).validate_data()

        if not self._shouldBeShown:
            return True

        if self._forceInput and self._input == '':
            return False

        return True

    def set_data(self, d):
        if self.enabled:
            self._input = d.get(self.name, '')

        if self._input == 'None':
            self._input = ''


class WebAudioElement(Element, WebElementInterface):
    def __init__(self, wav_url=None, wav_path=None, ogg_url=None, ogg_path=None, mp3_url=None, mp3_path=None, controls=True, autoplay=False, loop=False, **kwargs):
        '''
        TODO: Add docstring
        '''
        super(WebAudioElement, self).__init__(**kwargs)
        if wav_path is not None and not os.path.isabs(wav_path):
            wav_path = os.path.join(settings.general.external_files_dir, wav_path)
        if ogg_path is not None and not os.path.isabs(ogg_path):
            ogg_path = os.path.join(settings.general.external_files_dir, ogg_path)
        if mp3_path is not None and not os.path.isabs(mp3_path):
            mp3_path = os.path.join(settings.general.external_files_dir, mp3_path)

        self._wavPath = wav_path
        self._oggPath = ogg_path
        self._mp3Path = mp3_path

        self._wav_audio_url = wav_url
        self._ogg_audio_url = ogg_url
        self._mp3_audio_url = mp3_url

        self._controls = controls
        self._autoplay = autoplay
        self._loop = loop

        if self._wavPath is None and self._oggPath is None and self._mp3Path is None and self._wav_audio_url is None and self._ogg_audio_url is None and self._mp3_audio_url is None:
            raise AlfredError

    def prepare_web_widget(self):

        if self._wav_audio_url is None and self._wavPath is not None:
            self._wav_audio_url = self._question._experiment.user_interface_controller.add_static_file(self._wavPath)

        if self._ogg_audio_url is None and self._oggPath is not None:
            self._ogg_audio_url = self._question._experiment.user_interface_controller.add_static_file(self._oggPath)

        if self._mp3_audio_url is None and self._mp3Path is not None:
            self._mp3_audio_url = self._question._experiment.user_interface_controller.add_static_file(self._mp3Path)

    @property
    def web_widget(self):
        widget = '<div class="audio-element"><p class="%s"><audio %s %s %s><source src="%s" type="audio/mp3"><source src="%s" type="audio/ogg"><source src="%s" type="audio/wav">Your browser does not support the audio element</audio></p></div>' % (alignment_converter(self._alignment, 'both'), 'controls' if self._controls else '', 'autoplay' if self._autoplay else '', 'loop' if self._loop else '', self._mp3_audio_url, self._ogg_audio_url, self._wav_audio_url)

        return widget


class WebVideoElement(Element, WebElementInterface):
    def __init__(self, width=None, height=None, mp4_url=None, mp4_path=None, ogg_url=None, ogg_path=None, web_m_url=None, web_m_path=None, controls=True, autoplay=False, loop=False, **kwargs):
        '''
        TODO: Add docstring
        '''
        super(WebVideoElement, self).__init__(**kwargs)
        if mp4_path is not None and not os.path.isabs(mp4_path):
            mp4_path = os.path.join(settings.general.external_files_dir, mp4_path)
        if ogg_path is not None and not os.path.isabs(ogg_path):
            ogg_path = os.path.join(settings.general.external_files_dir, ogg_path)
        if web_m_path is not None and not os.path.isabs(web_m_path):
            web_m_path = os.path.join(settings.general.external_files_dir, web_m_path)

        self._mp4Path = mp4_path
        self._oggPath = ogg_path
        self._webMPath = web_m_path

        self._mp4_video_url = mp4_url
        self._ogg_video_url = ogg_url
        self._webM_video_url = web_m_url

        self._controls = controls
        self._autoplay = autoplay
        self._loop = loop
        self._width = width
        self._height = height

        if self._mp4Path is None and self._oggPath is None and self._webMPath is None and self._mp4_video_url is None and self._ogg_video_url is None and self._webM_video_url is None:
            raise AlfredError

    def prepare_web_widget(self):

        if self._mp4_video_url is None and self._mp4Path is not None:
            self._mp4_video_url = self._question._experiment.user_interface_controller.add_static_file(self._mp4Path)

        if self._ogg_video_url is None and self._oggPath is not None:
            self._ogg_video_url = self._question._experiment.user_interface_controller.add_static_file(self._oggPath)

        if self._webM_video_url is None and self._webMPath is not None:
            self._webM_video_url = self._question._experiment.user_interface_controller.add_static_file(self._webMPath)

    @property
    def web_widget(self):
        widget = '<div class="video-element"><p class="%s"><video %s %s %s %s %s><source src="%s" type="video/mp4"><source src="%s" type="video/ogg"><source src="%s" type="video/webM">Your browser does not support the video element</audio></p></div>' % (alignment_converter(self._alignment, 'both'), 'width="' + str(self._width) + '"' if self._width else '', 'height="' + str(self._height) + '"' if self._height else '', 'controls' if self._controls else '', 'autoplay' if self._autoplay else '', 'loop' if self._loop else '', self._mp4_video_url, self._ogg_video_url, self._webM_video_url)

        return widget


class ExperimenterMessages(TableElement):
    def prepare_web_widget(self):
        self._elements = []
        messages = self._question._experiment.experimenter_message_manager.get_messages()

        for message in messages:
            output = ''

            if not message.title == '':
                output = output + '<strong>' + message.title + '</strong> - '

            output = output + message.msg

            message.level = '' if message.level == 'warning' else 'alert-' + message.level

            message_element = TextElement('<div class="alert ' + message.level + '"><button type="button" class="close" data-dismiss="alert">&times;</button>' + output + ' </div>')

            message_element.added_to_page(self._question)

            self._elements.append([message_element])

        super(ExperimenterMessages, self).prepare_web_widget()


class WebExitEnabler(Element, WebElementInterface):
    @property
    def web_widget(self):
        widget = "<script>$(document).ready(function(){glob_unbind_leaving();});</script>"

        return widget
