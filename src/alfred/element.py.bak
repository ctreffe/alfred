# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

**element** contains general baseclass :class:`.element.Element` and its' children, which can be added to
:class:`.question.CompositeQuestion` (see table for an overview). It also contains abstract baseclasses for
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

import re
import string
import random
import json
from abc import ABCMeta, abstractmethod, abstractproperty
from os.path import abspath
from StringIO import StringIO
import os
import jinja2

from PySide.QtGui import QLabel, QHBoxLayout, QFont, QImage, QTextDocument, QWidget, QLineEdit, QSizePolicy, QPixmap, QLayout, QGridLayout, QProgressBar, QTextEdit, QVBoxLayout, QDoubleValidator, QButtonGroup, QRadioButton, QCheckBox, QFrame
from PySide.QtCore import Qt

from exceptions import AlfredError
from _helper import fontsizeConverter, alignmentConverter
import alfred.settings as settings
import question
from uuid import uuid4

import alfredlog
logger = alfredlog.getLogger(__name__)

class Element(object):
    '''
    **Description:** Baseclass for every element with basic arguments.

    :param str name: Name of Element.
    :param str alignment: Alignment of element in widget container ('left' as standard, 'center', 'right').
    :param str/int fontSize: Font size used in element ('normal' as standard, 'big', 'huge', or int value setting font size in pt).
    '''
    def __init__(self, name=None, shouldBeShownFilterFunction=None, **kwargs):
        if not (isinstance(self, WebElementInterface) or isinstance(self, QtElementInterface)):
            raise AlfredError("Element must implement WebElementInterface or QtElementInterface.")

        if name is not None:
            if not re.match('^%s$' % '[-_A-Za-z0-9]*', name):
                raise ValueError(u'Element names may only contain following charakters: A-Z a-z 0-9 _ -')

        self._name = name

        self._question = None
        self._enabled = True
        self._showCorrectiveHints = False
        self._shouldBeShown = True
        self._shouldBeShownFilterFunction = shouldBeShownFilterFunction if shouldBeShownFilterFunction is not None else lambda exp: True

        self._alignment = kwargs.pop('alignment', 'left')
        self._fontSize = kwargs.pop('fontSize', 'normal')
        self._maximumWidgetWidth = None

        if kwargs != {}:
            raise ValueError("Parameter '%s' is not supported." % kwargs.keys()[0])

    @property
    def name(self):
        '''
        Property **name** marks a general identifier for element, which is also used as variable name in experimental datasets.
        Stored input data can be retrieved from dictionary returned by :meth:`.dataManager.DataManager.getData`.
        '''
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, str):
            raise TypeError
        self._name = name

    @property
    def maximumWidgetWidth(self):
        return self._maximumWidgetWidth

    @maximumWidgetWidth.setter
    def maximumWidgetWidth(self, maximumWidgetWidth):
        if not isinstance(maximumWidgetWidth, int):
            raise TypeError
        self._maximumWidgetWidth = maximumWidgetWidth


    def addedToQuestion(self, q):
        if not isinstance(q, question.Question):
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
    def canDisplayCorrectiveHintsInline(self):
        return False

    @property
    def alignment(self):
        return self._alignment

    @property
    def correctiveHints(self):
        return []

    @property
    def showCorrectiveHints(self):
        return self._showCorrectiveHints

    @showCorrectiveHints.setter
    def showCorrectiveHints(self, b):
        self._showCorrectiveHints = bool(b)

    def validateData(self):
        return True

    def setShouldBeShownFilterFunction(self, f):
        """
        Sets a filter function. f must take Experiment as parameter
        :type f: function
        """
        self._shouldBeShownFilterFunction = f

    def removeShouldBeShownFilterFunction(self):
        """
        remove the filter function
        """
        self._shouldBeShownFilterFunction = lambda exp: True

    @property
    def shouldBeShown(self):
        """
        Returns True if shouldBeShown is set to True (default) and all shouldBeShownFilterFunctions return True.
        Otherwise False is returned
        """
        return self._shouldBeShown and self._shouldBeShownFilterFunction(self._question._experiment)

    @shouldBeShown.setter
    def shouldBeShown(self, b):
        """
        sets shouldBeShown to b.

        :type b: bool
        """
        if not isinstance(b, bool):
            raise TypeError("shouldBeShown must be an instance of bool")
        self._shouldBeShown = b

class WebElementInterface(object):
    '''
    Abstract class **WebElementInterface** contains properties and methods allowing elements to be used and displayed
    in experiments of type 'web'.
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def webWidget(self):
        pass

    def prepareWebWidget(self):
        pass

    @property
    def webThumbnail(self):
        return None

    def setData(self, data):
        pass

    @property
    def cssCode(self):
        return []
    @property
    def cssURLs(self):
        return []

    @property
    def jsCode(self):
        return []

    @property
    def jsURLs(self):
        return []

class QtElementInterface(object):
    '''
    Abstract class **QtElementInterface** contains properties and methods allowing elements to be used  and displayed
    in experiments of type 'qt'.
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def qtWidget(self):
        pass

    def prepareQtWidget(self):
        pass

    @property
    def qtThumbnail(self):
        return None


class HorizontalLine(Element, WebElementInterface, QtElementInterface):
    def __init__(self, strength=1, color='black', **kwargs):
        '''
        **HorizontalLine** allows display of a simple divider in questions.

        :param int strength: Set line thickness (in pixel).
        :param str color: Set line color (color argument as string).
        '''
        super(HorizontalLine, self).__init__(**kwargs)

        self._strength = strength
        self._color = color
        self._elementQtWidget = None

    @property
    def webWidget(self):

        widget = '<hr class="horizontal-line" style="%s %s">' % ('height: %spx;'% self._strength, 'background-color: %s;'% self._color)

        return widget

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            '''
            The following QWidget adjusts to maximumWidgetWidth. 
            '''
            self._elementQtWidget = QWidget()
            line_palette = self._elementQtWidget.palette()
            line_palette.setColor(self._elementQtWidget.backgroundRole(), self._color)
            self._elementQtWidget.setPalette(line_palette)
            self._elementQtWidget.setAutoFillBackground(True)
            self._elementQtWidget.setMinimumSize(self._maximumWidgetWidth,self._strength) # Set element width depending on layout width
            self._elementQtWidget.setMaximumSize(self._maximumWidgetWidth,self._strength)

        return self._elementQtWidget

class ProgressBar(Element, WebElementInterface, QtElementInterface):
    def __init__(self, instruction='', barRange=(0,100), barValue=50, barWidth=None, instructionWidth=None, instructionHeight=None, **kwargs):
        '''
        **ProgressBar** allows display of a manually controlled progress bar.
        '''
        super(ProgressBar, self).__init__(**kwargs)

        self._instruction = instruction
        self._instructionWidth = instructionWidth
        self._instructionHeight = instructionHeight
        self._barRange = barRange
        self._barValue = float(barValue)

        if barWidth:
            self._barWidth = barWidth
        else:
            self._barWidth = None

        self._elementQtWidget = None
        self._progressBar = None

    @property
    def barValue(self):
        return self._barValue

    @barValue.setter
    def barValue(self, value):
        self._barValue = value
        if self._progressBar:
            self._progressBar.setValue(self._barValue)
            self._progressBar.repaint()

    @property
    def webWidget(self):
        if self._barRange[1]-self._barRange[0] == 0:
            raise ValueError('barRange in web progress bar must be greater than 0')

        widget = '<div class="progress-bar"><table class="%s" style="font-size: %spt;">' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize))

        widget = widget+'<tr><td><table class="%s"><tr><td style="%s %s">%s</td>' % (alignmentConverter(self._alignment, 'container'), 'width: %spx;' %self._instructionWidth if self._instructionWidth is not None else "", 'height: %spx;' %self._instructionHeight if self._instructionHeight is not None else "", self._instruction)

        widget = widget + '<td><meter value="%s" min="%s" max="%s" style="font-size: %spt; width: %spx; margin-left: 5px;"></meter></td>' % (self._barValue, self._barRange[0], self._barRange[1], fontsizeConverter(self._fontSize)+5, self._barWidth if self._barWidth is not None else '200')

        widget = widget + '<td style="font-size: %spt; padding-left: 5px;">%s</td>' % (fontsizeConverter(self._fontSize), str(int(self._barValue/(self._barRange[1]-self._barRange[0])*100))+'%')

        widget = widget + '</tr></table></td></tr></table></div>'

        return widget

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            # Setting font size
            fontSize = fontsizeConverter(self._fontSize)

            # Creating progress bar
            self._progressBar = QProgressBar()
            self._progressBar.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)

            self._progressBar.setRange(self._barRange[0],self._barRange[1])
            self._progressBar.setValue(self._barValue)
            self._progressBar.adjustSize()

            if self._barWidth:
                self._progressBar.setFixedWidth(self._barWidth)


            # Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth-(self._progressBar.width()+10):
                tempWidth = self._maximumWidgetWidth-(self._progressBar.width()+10)

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+2 # +2 for margins.

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting text alignment
            self._instructionText.setAlignment(Qt.AlignLeft|Qt.AlignBottom)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter|Qt.AlignBottom)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight|Qt.AlignBottom)


            # Erstellung des eigentlichen ElementWidget
            progressBarLayout = QHBoxLayout()
            progressBarLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            progressBarLayout.setSpacing(5)
            progressBarLayout.addWidget(self._instructionText)
            progressBarLayout.addWidget(self._progressBar)
            progressBarLayout.setAlignment(self._progressBar,Qt.AlignBottom)

            # Einstellen der inneren Elementausrichtung
            if self._alignment == 'center':
                progressBarLayout.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                progressBarLayout.setAlignment(Qt.AlignRight)
            else:
                progressBarLayout.setAlignment(Qt.AlignLeft)

            # Erstellung des äußeren Containers für ElementWidget und CorrectiveHints         
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.addLayout(progressBarLayout)

            # Erstellung des finalen Widgets
            self._elementQtWidget = QWidget()
            self._elementQtWidget.setLayout(outerWidgetLayout)

        return self._elementQtWidget

class TextElement(Element, WebElementInterface, QtElementInterface):
    def __init__(self, text, textWidth=None, textHeight=None, **kwargs):
        '''
        **TextElement** allows display of simple text labels and partially supports rich text in qt.

        :param str text: Text to be displayed by TextElement (can contain html commands).
        :param str alignment: Alignment of TextElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Fontsize used in TextElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param int textWidth: Set the width of the label to a fixed size, still allowing for word wrapping and growing height of text.
        :param int textHeight: Set the height of the label to a fixed size (sometimes necessary when using rich text).
        '''
        super(TextElement, self).__init__(**kwargs)

        self._text = text
        self._textWidth = textWidth
        self._textHeight = textHeight
        self._elementQtWidget = None
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
    def webWidget(self):
        widget = '<div class="text-element"><p class="%s" style="font-size: %spt; %s %s">%s</p></div>' % (alignmentConverter(self._alignment, 'both'), fontsizeConverter(self._fontSize), 'width: %spx;'% self._textWidth if self._textWidth is not None else "", 'height: %spx;'% self._textHeight if self._textHeight is not None else "", self._text)

        return widget

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            # Setting font size
            fontSize = fontsizeConverter(self._fontSize)

            # Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._text)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._textLabel = QLabel(self._text)

            self._textLabel.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._textLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)

            self._textLabel.adjustSize() #Updates label to correct size

            fontMetrics = self._textLabel.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._textWidth:
                tempWidth = self._textWidth

            self._textLabel.setFixedWidth(tempWidth)

            self._textLabel.adjustSize() #Updates label to correct size

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+2 # +2 for margins

            if self._textHeight:
                tempHeight = self._textHeight

            self._textLabel.setFixedHeight(tempHeight)

            # Setting text alignment
            self._textLabel.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._textLabel.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._textLabel.setAlignment(Qt.AlignRight)

            self._elementQtWidget = self._textLabel #Setting final widget

        return self._elementQtWidget


class DataElement(Element, WebElementInterface, QtElementInterface):
    def __init__(self, variable, **kwargs):
        '''
        **DataElement** returns no widget, but can save a variable of any type into experiment data.

        :param str variable: Variable to be stored into experiment data.
        '''
        super(DataElement, self).__init__(**kwargs)
        self._variable = variable
        self._elementQtWidget = None

    @property
    def variable(self):
        return self._variable

    @variable.setter
    def variable(self, variable):
        self._variable = variable

    @property
    def webWidget(self):
        return ''

    @property
    def qtWidget(self):

        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()
            self._elementQtWidget.hide()

        return self._elementQtWidget

    @property
    def data(self):
        return {self.name: self._variable}

class InputElement(Element):
    '''
    Class **InputElement** is the base class for any element allowing data input.

    :param bool forceInput: Sets user input to be mandatory (False as standard or True).
    :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.

    .. todo:: Parent class :class:`.element.Element` has method *correctiveHints()*, but not sure why this is necessary, since correctiveHints only make sense in input elements, right?
    '''
    def __init__(self, forceInput=False, noInputCorrectiveHint=None, debugString=None, debugValue=None, default=None, **kwargs):
        super(InputElement, self).__init__(**kwargs)
        self._input = ''
        self._forceInput = forceInput
        self._noInputCorrectiveHint = noInputCorrectiveHint
        self._debugString = debugString
        self._debugValue = debugValue

        if settings.debugmode and settings.debug.defaultValues:
            if self._debugValue:
                self._input = self._debugValue
            elif not self._debugString:
                self._input = settings.debug.get(self.__class__.__name__)
            else:
                self._input = settings._config_parser.get('debug',debugString)

        if default is not None:
            self._input = default

    def validateData(self):
        return not self._forceInput or not self._shouldBeShown or bool(self._input)

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []
        if self._forceInput and self._input == '':
            return [self.no_input_hint]
        else:
            return super(InputElement, self).correctiveHints

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
            if hints.has_key(noInputName):
                return hints[noInputName]

        logger.error("Can't access default no input hint for element %s" % self)
        return "Can't access default no input hint for element %s" % type(self).__name__


    @property
    def data(self):
        return {self.name: self._input}

    def setData(self, d):
        if self.enabled:
            self._input = d.get(self.name, '')


class TextEntryElement(InputElement, WebElementInterface, QtElementInterface):
    def __init__(self, instruction='', noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, prefix=None, suffix=None, **kwargs):
        '''
        **TextEntryElement*** returns a single line text edit with an instruction text on its' left.

        :param str name: Name of TextEntryElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param int instructionWidth: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instructionHeight: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of TextEntryElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Font size used in TextEntryElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''
        super(TextEntryElement, self).__init__(noInputCorrectiveHint = noInputCorrectiveHint, **kwargs)

        self._instructionWidth = instructionWidth
        self._instructionHeight = instructionHeight
        self._instruction = instruction
        self._elementQtWidget = None
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
    def webWidget(self):

        d = {}
        d['alignment'] = alignmentConverter(self._alignment, 'container')
        d['fontsize'] = fontsizeConverter(self._fontSize)
        d['width'] = self._instructionWidth
        d['height'] = self._instructionHeight
        d['instruction'] = self._instruction
        d['name'] = self.name
        d['input'] = self._input
        d['disabled'] = not self.enabled
        d['prefix'] = self._prefix
        d['suffix'] = self._suffix
        if self.correctiveHints:
            d['corrective_hint'] = self.correctiveHints[0]
        return self._template.render(d)

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            #Setting font size
            fontSize = fontsizeConverter(self._fontSize)

            #Creating LineEdits 
            self._textEntry = QLineEdit()
            self._textEntry.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
            self._textEntry.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt; background-color: white; margin-bottom: -2px;' % fontSize)
            self._textEntry.setPlaceholderText('Bitte Eingeben')
            self._textEntry.adjustSize()

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth-(self._textEntry.width()+10):
                tempWidth = self._maximumWidgetWidth-(self._textEntry.width()+10)

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+2 # +2 for margins.

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting text alignment
            self._instructionText.setAlignment(Qt.AlignLeft|Qt.AlignBottom)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter|Qt.AlignBottom)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight|Qt.AlignBottom)

            #Creating corrective hint
            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            # Erstellung des eigentlichen ElementWidget
            textEntryLayout = QHBoxLayout()
            textEntryLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            textEntryLayout.setSpacing(5)
            textEntryLayout.addWidget(self._instructionText)
            textEntryLayout.addWidget(self._textEntry)
            textEntryLayout.setAlignment(self._textEntry,Qt.AlignBottom)

            # Einstellen der inneren Elementausrichtung
            if self._alignment == 'center':
                textEntryLayout.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                textEntryLayout.setAlignment(Qt.AlignRight)
            else:
                textEntryLayout.setAlignment(Qt.AlignLeft)

            # Erstellung des äußeren Containers für ElementWidget und CorrectiveHints         
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.addLayout(textEntryLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)
            outerWidgetLayout.setAlignment(self._correctiveHint,Qt.AlignRight)

            # Erstellung des finalen Widgets
            self._elementQtWidget = QWidget()
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._textEntry.setText(str(self._input))

        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird

        self._textEntry.setEnabled(self.enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()

        return self._elementQtWidget

    @property
    def canDisplayCorrectiveHintsInline(self):
        return True

    def validateData(self):
        super(TextEntryElement, self).validateData()

        if self._forceInput and self._shouldBeShown and self._input == '':
            return False

        return True

    def setData(self, d):
        '''
        .. todo:: No data can be set when using qt interface (compare web interface functionality). Is this a problem?
        '''
        if self.enabled:
            if d == 'qt':
                self._input = self._textEntry.text()
            else:
                super(TextEntryElement, self).setData(d)



class TextAreaElement(TextEntryElement):
    def __init__(self, instruction='', xSize=300, ySize=150, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, **kwargs):
        '''
        **TextAreaElement** returns a multiline text edit with an instruction on top.

        :param str name: Name of TextAreaElement and stored input variable.
        :param str instruction: Instruction to be displayed above multiline edit field (can contain html commands).
        :param int instructionWidth: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instructionHeight: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param int xSize: Horizontal size for visible text edit field in pixels.
        :param int ySize: Vertical size for visible text edit field in pixels.
        :param str alignment: Alignment of TextAreaElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in TextAreaElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.

        .. todo:: qt corrective hint always shown!
        '''
        super(TextAreaElement, self).__init__(instruction, noInputCorrectiveHint=noInputCorrectiveHint, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

        self._xSize = xSize
        self._ySize = ySize


    @property
    def webWidget(self):

        widget = '<div class="text-area-element"><table class="%s" style="font-size: %spt;">' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize))

        widget = widget + '<tr><td class="itempagination-left" style="padding-bottom: 10px;">%s</td></tr>' % (self._instruction)

        widget =  widget + '<tr><td class="%s"><textarea class="text-input pagination-left" style="font-size: %spt; height: %spx; width: %spx;" name="%s" %s>%s</textarea></td></tr>' % (alignmentConverter(self._alignment), fontsizeConverter(self._fontSize), self._ySize, self._xSize, self.name, "" if self.enabled else " disabled=\"disabled\"", self._input)

        if self.correctiveHints:
            widget = widget +  '<tr><td class="corrective-hint %s" style="font-size: %spt;">%s</td></tr>' % (alignmentConverter(self._alignment, 'both'), fontsizeConverter(self._fontSize)-1, self.correctiveHints[0])

        widget = widget + '</table></div>'

        return widget

    @property
    def cssCode(self):
        return [(99,".TextareaElement { resize: none; }")]

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            # Einstellen der Schriftgröße
            fontSize = fontsizeConverter(self._fontSize)

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.minimumSizeHint() #Somehow (?) updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+12 # +2 for margins. +10 for layout purposes

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting text alignment
            self._instructionText.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight)

            self._textEntry = QTextEdit()
            self._textEntry.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
            self._textEntry.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt; background-color: white;' % fontSize)
            self._textEntry.setFixedSize(self._xSize,self._ySize)

            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            #Erstellung des eigentlichen ElementWidget
            textEntryLayout = QVBoxLayout()
            textEntryLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            textEntryLayout.addWidget(self._instructionText)
            textEntryLayout.addWidget(self._textEntry)

            # Einstellen der inneren Elementausrichtung
            if self._alignment == 'center':
                textEntryLayout.setAlignment(self._instructionText, Qt.AlignHCenter)
                textEntryLayout.setAlignment(self._textEntry, Qt.AlignHCenter)
            elif self._alignment == 'right':
                textEntryLayout.setAlignment(self._instructionText, Qt.AlignRight)
                textEntryLayout.setAlignment(self._textEntry, Qt.AlignRight)
            else:
                textEntryLayout.setAlignment(self._instructionText, Qt.AlignLeft)
                textEntryLayout.setAlignment(self._textEntry, Qt.AlignLeft)

            #Erstellung des äußeren Containers für ElementWidget und CorrectiveHints         
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.addLayout(textEntryLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)

            # Ausrichten der corrective Hints
            if self._alignment == 'center':
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignHCenter)
            elif self._alignment == 'right':
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignRight)
            else:
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignLeft)

            # Erstellung des finalen Widgets
            self._elementQtWidget = QWidget()
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            self._textEntry.setText(self._input)

        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird
        self._textEntry.setEnabled(self.enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()

        return self._elementQtWidget

    def setData(self, d):
        if self.enabled:
            if d == 'qt':
                self._input = self._textEntry.toPlainText()
            else:
                super(TextAreaElement, self).setData(d)


class RegEntryElement(TextEntryElement):
    def __init__(self, instruction='', regEx ='.*', noInputCorrectiveHint=None, matchHint=None, instructionWidth=None, instructionHeight=None, **kwargs):
        '''
        **RegEntryElement*** displays a line edit, which only accepts Patterns that mach a predefined regular expression. Instruction is shown
        on the left side of the line edit field.

        :param str name: Name of TextAreaElement and stored input variable.
        :param str instruction: Instruction to be displayed above multiline edit field (can contain html commands).
        :param str regEx: Regular expression to match with user input.
        :param str alignment: Alignment of TextAreaElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in TextAreaElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        super(RegEntryElement, self).__init__(instruction, noInputCorrectiveHint=noInputCorrectiveHint, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

        self._regEx = regEx
        self._matchHint = matchHint

    def validateData(self):
        super(RegEntryElement, self).validateData()

        if not self._shouldBeShown:
            return True

        if not self._forceInput and self._input == '':
            return True

        if re.match('^%s$' % self._regEx, unicode(self._input)):
            return True

        return False

    @property
    def match_hint(self):
        if self._matchHint is not None:
            return self._matchHint
        if self._question and self._question._experiment\
                and self._question._experiment.settings.hints.has_key('corrective_regentry'):
            return self._question._experiment.settings.hints['corrective_regentry']
        logger.error("Can't access match_hint for %s " % type(self).__name__)
        return "Can't access match_hint for %s " % type(self).__name__

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []
        elif re.match('^%s$' % self._regEx, self._input):
            return []
        elif self._input == '' and not self._forceInput:
            return []
        elif self._input == '' and self._forceInput:
            return [self.no_input_hint]
        else:
            return [self.match_hint]

class NumberEntryElement(RegEntryElement):
    def __init__(self, instruction='', decimals = 0, min=None, max=None, noInputCorrectiveHint = None, instructionWidth=None, instructionHeight=None, matchHint=None, **kwargs):
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
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.

        .. todo:: qt corrective hint always shown!
        '''
        super(NumberEntryElement, self).__init__(instruction, noInputCorrectiveHint=noInputCorrectiveHint, instructionWidth=instructionWidth, instructionHeight=instructionHeight, matchHint=matchHint, **kwargs)

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
    def webWidget(self):

        d = {}
        d['alignment'] = alignmentConverter(self._alignment, 'container')
        d['fontsize'] = fontsizeConverter(self._fontSize)
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
        if self.correctiveHints:
            d['corrective_hint'] = self.correctiveHints[0]
        return self._template.render(d)


    def validateData(self):
        '''
        '''
        super(NumberEntryElement, self).validateData()

        if not self._shouldBeShown:
            return True

        if not self._forceInput and self._input == '':
            return True

        try:
            f = float(self._input)
        except:
            return False

        if self._min is not None:
            if not self._min <= f:
                return False

        if self._max is not None:
            if not f <= self._max:
                return False
                
        re_str = "^[+-]?\d+$" if self._decimals == 0 else "^[+-]?(\d*[.,]\d{1,%s}|\d+)$" % self._decimals
        if re.match(re_str, str(self._input)):
            return True

        return False

    @property
    def data(self):
        if 0 < self._decimals:
            try:
                tempInput = float(self._input)
            except:
                tempInput = ''
        else:
            try:
                tempInput = int(self._input)
            except:
                tempInput = ''

        return({self.name: tempInput} if self.validateData() and tempInput != '' else {self.name: ''})

    def setData(self, d):
        if self.enabled:
            if d == 'qt':
                val = self._textEntry.text()
                if not isinstance(val, str) and not isinstance(val, unicode):
                    val = str(val)
                val = val.replace(',','.')

                self._input = val

            else:
                val = d.get(self.name, '')
                if not isinstance(val, str) and not isinstance(val, unicode):
                    val = str(val)
                val = val.replace(',','.')
                super(NumberEntryElement, self).setData({self.name: val})


    @property
    def qtWidget(self):
        self._elementQtWidget = super(NumberEntryElement, self).qtWidget

        if self._validator == None:
            self._validator = QDoubleValidator()
            self._validator.setDecimals(self._decimals)

            if not self._min == None:
                self._validator.setBottom(self._min)

            if not self._max == None:
                self._validator.setTop(self._max)

            self._textEntry.setValidator(self._validator)

        return self._elementQtWidget

    @property
    def match_hint(self):
        if self._matchHint is not None:
            return self._matchHint

        if self._question and self._question._experiment\
                and self._question._experiment.settings.hints.has_key('corrective_numberentry'):
            return self._question._experiment.settings.hints['corrective_numberentry']
        logger.error("Can't access match_hint for %s " % type(self).__name__)
        return "Can't access match_hint for %s " % type(self).__name__


    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []

        elif self._input == '' and not self._forceInput:
            return []

        elif self._forceInput and self._input == '':
            return [self.no_input_hint]
        else:
            re_str = "^[+-]?\d+$" if self._decimals == 0 else "^[+-]?(\d*[.,]\d{1,%s}|\d+)$" % self._decimals
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
    def __init__(self, instruction='', password='', forceInput=True, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, **kwargs):
        '''
        **PasswordElement*** desplays a single line text edit for entering a password (input is not visible) with an instruction text on its' left.

        :param str name: Name of PasswordElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param str password: Password to be matched against user input.
        :param int spacing: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of PasswordElement in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in PasswordElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (True as standard or False).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.

        .. caution:: If forceInput is set to false, any input will be accepted, but still validated against correct password.
        '''
        super(PasswordElement, self).__init__(instruction, noInputCorrectiveHint=noInputCorrectiveHint, forceInput=forceInput, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

        self._password = password

    @property
    def webWidget(self):

        widget = '<div class="text-entry-element"><table class="%s" style="font-size: %spt;">' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize))

        widget = widget+'<tr><td valign="bottom"><table class="%s"><tr><td %s>%s</td>' % (alignmentConverter(self._alignment, 'container'), 'style="width: %spx;"' %self._instructionWidth if self._instructionWidth is not None else "", self._instruction)

        widget = widget + '<td valign="bottom"><input class="text-input" type="password" style="font-size: %spt; margin-bottom: 0px; margin-left: 5px;" name="%s" value="%s" %s /></td></tr></table></td></tr>' % (fontsizeConverter(self._fontSize), self.name, self._input, "" if self.enabled else 'disabled="disabled"')

        if self.correctiveHints:
            widget = widget +  '<tr><td><table class="corrective-hint containerpagination-right"><tr><td style="font-size: %spt;">%s</td></tr></table></td></tr>' % (fontsizeConverter(self._fontSize), self.correctiveHints[0])

        widget = widget + '</table></div>'

        return widget

    @property
    def qtWidget(self):
        self._elementQtWidget = super(PasswordElement, self).qtWidget

        self._textEntry.setEchoMode(QLineEdit.Password)

        return self._elementQtWidget

    def validateData(self):
        super(PasswordElement, self).validateData()

        if not self._forceInput or not self._shouldBeShown:
            return True

        return self._input == self._password

    @property
    def wrong_password_hint(self):
        if self._question and self._question._experiment\
                and self._question._experiment.settings.hints.has_key('corrective_password'):
            return self._question._experiment.settings.hints['corrective_password']
        logger.error("Can't access wrong_password_hint for %s " % type(self).__name__)
        return "Can't access wrong_password_hint for %s " % type(self).__name__

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
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

class LikertMatrix(InputElement, WebElementInterface, QtElementInterface):
    def __init__(self, instruction='', levels=7, items=4, topScaleLabels=None,
                 bottomScaleLabels = None, itemLabels = None, itemLabelWidth = None, spacing=30,
                 transpose = False, noInputCorrectiveHint=None, tableStriped=False, shuffle=False,
                 instructionWidth=None, instructionHeight=None, useShortLabels=False, **kwargs):
        '''
        **LikertMatrix** displays a matrix of multiple likert items with adjustable scale levels per item.
        Instruction is shown above element.

        :param str name: Name of LikertMatrix and stored input variable.
        :param str instruction: Instruction to be displayed above likert matrix (can contain html commands).
        :param int levels: Number of scale levels.
        :param int items: Number of items in matrix (rows or columns if transpose = True).
        :param list topScaleLabels: Labels for each scale level on top of the Matrix.
        :param list bottomScaleLabels: Labels for each scale level under the Matrix.
        :param list itemLabels: Labels for each item on both sides of the scale.
        :param int spacing: Sets column width or row height (if transpose set to True) in likert matrix, can be used to ensure symmetric layout.
        :param bool transpose: If set to True matrix is layouted vertically instead of horizontally.
        :param str alignment: Alignment of LikertMatrix in widget container ('left' as standard, 'center', 'right').
        :param str/int font: Fontsize used in LikertMatrix ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        super(LikertMatrix, self).__init__(noInputCorrectiveHint=noInputCorrectiveHint, **kwargs)

        if spacing < 30:
            raise ValueError('Spacing must be greater or equal than 30!')

        self._instruction = instruction
        self._instructionWidth = instructionWidth
        self._instructionHeight = instructionHeight
        self._levels = levels
        self._items = items
        self._itemLabelWidth = itemLabelWidth
        self._spacing = spacing
        self._tableStriped = tableStriped
        self._transpose = transpose
        self._useShortLabels = useShortLabels

        self._defaultSet = False

        self._permutation = range(items)
        if shuffle:
            random.shuffle(self._permutation)

        if topScaleLabels is not None and not len(topScaleLabels) == self._levels:
            raise ValueError(u"Es mussen keine oder %s OBERE (bei Transpose LINKE) Skalenlabels ubergeben werden." % self._levels)
        self._topScaleLabels = topScaleLabels

        self._elementQtWidget = None

        if bottomScaleLabels is not None and not len(bottomScaleLabels) == self._levels:
            raise ValueError(u"Es mussen keine oder %s UNTERE (bei Transpose RECHTE) Skalenlabels ubergeben werden." % self._levels)
        self._bottomScaleLabels = bottomScaleLabels

        if itemLabels is not None and not len(itemLabels) == (2*self._items):
            raise ValueError(u"Es mussen keine oder %s Itemlabels ubergeben werden." % (2*self._items))
        self._itemLabels = itemLabels

        if settings.debugmode and settings.debug.defaultValues:
            self._input = [str(int(self._input)-1) for i in range(self._items)]
        elif not self._input == '':
            self._input = [str(int(self._input)-1) for i in range(self._items)]
            self._defaultSet = True
        else:
            self._input = ['-1' for i in range(self._items)]


    @property
    def canDisplayCorrectiveHintsInline(self):
        return True

    @property
    def data(self):
        lmData = {}
        for i in range(self._items):
            label = self.name + '_' + str(i+1)
            if self._useShortLabels:
                short_labels = self._short_labels()
                label += '_' + short_labels[i]
            lmData.update({label: None if int(self._input[i])+1 == 0 else int(self._input[i])+1})
        lmData[self.name + '_permutation'] = [i+1 for i in self._permutation]
        return lmData

    def _short_labels(self):
        l = 6
        rv = []
        for i in range(self._items):
            label = self._itemLabels[2*i]
            if label != '':
                label = label.replace('.', '')
                words = label.split()
                num = int(round((l / len(words)) + 0.5))
                sl = ''
                for w in words:
                    sl = sl + w[:num]
                rv.append(sl[:l])
            else:
                rv.append('')
        return rv

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()

            fontSize = fontsizeConverter(self._fontSize) # Converting fontSize into valid argument

            maximumLeftLabelWidth = 0 # Variable will be used to determine uniform width of left item labels
            maximumRightLabelWidth = 0 # Variable will be used to determine uniform width of right item labels

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+12 # +2 for margins. +10 for layout purposes

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting instruction text alignment
            self._instructionText.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight)

            # Creating central likert matrix layout

            self._likertLayout = QGridLayout()
            self._likertLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom

            if not self._transpose:
                '''
                The following part constructs the likert matrix without transposing. Different items are therefore
                shown in the vertical axis while different likert levels for each item are shown in the horizontal axis.
                '''

                # Setting general cell spacing

                self._likertLayout.setVerticalSpacing(0)
                self._likertLayout.setHorizontalSpacing(0)

                labelWidthList = [] # Will be used to determine necessary cell width for each column of the likert matrix
                labelHeightList = [] # Will be used to determine necessary cell height for each row of the likert matrix

                if self._topScaleLabels: #Top scale labels are shown directly above the first row of radio buttons
                    i = 1
                    for label in self._topScaleLabels: # Each label is processed separately
                        cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                        cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(2,2,2,2) # No margins in cell layout
                        cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for top labels

                        tLabel = QLabel(label) # Creating a specific top scale label
                        tLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        tLabel.setAlignment(Qt.AlignCenter) # Top scale labels will be centered above radio buttons
                        tLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                        fontMetrics = tLabel.fontMetrics() # Gathering information on label size given the chosen font
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", label)
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)


                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                        if tempWidth < self._spacing: # Top scale labels have to be at least as wide as spacing argument
                            tempWidth = self._spacing

                        labelWidthList.append(tempWidth)

                        cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                        cellLayout.addWidget(tLabel) # Adding label to cell layout 
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame,0, i, 1,1, alignment=4) # Adding top scale label frame to correct cell in first row of likert matrix
                        self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter) # Center alignment for top scale label frames
                        i=i+1

                for i in range (self._items): # Beginning new row for each likert item in matrix
                    vars(self)['buttonGroup_'+str(self._permutation[i])] = QButtonGroup(self._elementQtWidget) # Creating new button group for item using the permutated item list in case of shuffle

                    if self._itemLabels: # Item labels are shown left and right of each likert item in the matrix
                        cellFrame = QFrame() # Creating an empty frame for item label
                        if i%2 == 0 and self._tableStriped: # Setting different background color to all odd rows if tableStriped flag is set
                            cellFrame.setStyleSheet('background-color: white;')

                        cellLayout = QVBoxLayout() # New layout for label cell
                        cellLayout.setSpacing(0)
                        cellLayout.setContentsMargins(2,2,2,2)
                        cellLayout.setAlignment(Qt.AlignRight|Qt.AlignVCenter) # All left item labels will be aligned right

                        lLabel = QLabel(self._itemLabels[self._permutation[i]*2]) # Creating the actual item label using the permutation list in case of shuffle
                        lLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        lLabel.adjustSize() # Update label size for correct layouting

                        fontMetrics = lLabel.fontMetrics() # Gathering font size information
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[self._permutation[i]*2])
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Calculating necessary label size for correct display of itemlabel plus margin

                        tempHeight = fontMetrics.size(0,temp_label_text).height()+4 # plus margin
                        labelHeightList.append(tempHeight)

                        if self._itemLabelWidth: # If argument is used tempWidth is overwritten by itemLabelWidth argument
                            tempWidth = self._itemLabelWidth

                        cellFrame.setFixedWidth(tempWidth) # Setting width for label
                        lLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter) # Left item label text alignment is set to right

                        if maximumLeftLabelWidth < tempWidth: # The following code determines the widest left itemlabel to give all item labels a uniform width
                            maximumLeftLabelWidth = tempWidth

                        cellLayout.addWidget(lLabel) # Adding label to cell frame
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, i+1, 0, 1, 1, alignment=4)
                        self._likertLayout.setAlignment(cellFrame, Qt.AlignRight|Qt.AlignVCenter) # Left item label frames are aligned right

                    for j in range(self._levels): #Adding Radiobuttons for each sclae level in each likert item
                        cellFrame = QFrame() # New empty frame for each radio button

                        if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                            cellFrame.setStyleSheet('background-color: white;')
                        cellFrame.setFixedWidth(self._spacing) # Radio button frames need to be at leas as wide as spacing argument

                        cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(0,0,0,0) # No margins around cell layout

                        vars()['button_'+str(self._permutation[i])+'_'+str(j)] = QRadioButton() # Creating the actual radio button using permutation list in case of shuffle
                        vars()['button_'+str(self._permutation[i])+'_'+str(j)].setStyleSheet('QRadioButton{width: 0px; height: 0px; padding-left: 6px;} QRadioButton::indicator{width: 15px; height: 15px;}') # Disabling text label in QRadioButton and centering indicator
                        vars()['button_'+str(self._permutation[i])+'_'+str(j)].adjustSize()

                        vars(self)['buttonGroup_'+str(self._permutation[i])].addButton(vars()['button_'+str(self._permutation[i])+'_'+str(j)], j) # Button is added to correct button group using permutation list

                        cellLayout.addWidget(vars()['button_'+str(self._permutation[i])+'_'+str(j)])
                        cellLayout.setAlignment(vars()['button_'+str(self._permutation[i])+'_'+str(j)], Qt.AlignCenter) # Radio buttons in cells are centered
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, i+1, j+1, 1, 1, alignment=4) # Button is added to likert matrix with center alignment
                        self._likertLayout.setAlignment(cellFrame, Qt.AlignCenter) # RadioButtons are being centered

                    if self._itemLabels: # Item labels are shown left and right of each likert item in the matrix
                        cellFrame = QFrame() # Creating an empty frame for item label
                        if i%2 == 0 and self._tableStriped: # Setting different background color to all odd rows if tableStriped flag is set
                            cellFrame.setStyleSheet('background-color: white;')

                        cellLayout = QVBoxLayout() # New layout for label cell
                        cellLayout.setSpacing(0)
                        cellLayout.setContentsMargins(2,2,2,2)
                        cellLayout.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # Alle right item labels will be aligned left

                        rLabel = QLabel(self._itemLabels[(self._permutation[i]+1)*2-1]) # Creating actual right item label using permutation list in case of shuffle
                        rLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        rLabel.adjustSize() # Updating label size information for correct layouting

                        fontMetrics = rLabel.fontMetrics() # Gathering font size information
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[(self._permutation[i]+1)*2-1])
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Calculating necessary label size for correct display of itemlabel plus margin.

                        if self._itemLabelWidth: # If argument is used tempWidth is overwritten by itemLabelWidth argument
                            tempWidth = self._itemLabelWidth

                        tempHeight = fontMetrics.size(0,temp_label_text).height()+4 # plus margin

                        if labelHeightList[i] < tempHeight: # Deciding if right or left item label is higher
                            labelHeightList[i] = tempHeight

                        cellFrame.setFixedWidth(tempWidth) # Setting width for label
                        rLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # Right item label text alignment is set to left

                        if maximumRightLabelWidth < tempWidth: # The following code determines the widest right itemlabel to give all item labels a uniform width
                            maximumRightLabelWidth = tempWidth

                        cellLayout.addWidget(rLabel) # Adding label to cell frame
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, i+1, self._levels+1, 1, 1, alignment=4) # Adding right item label to correct cell in likert matrix
                        self._likertLayout.setAlignment(cellFrame, Qt.AlignLeft|Qt.AlignVCenter) # Right item label frames are aligned left

                if self._bottomScaleLabels:
                    i = 1

                    for label in self._bottomScaleLabels: # Each label is processed separately
                        cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                        cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(2,2,2,2) # No margins in cell layout
                        cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for bottom labels

                        bLabel = QLabel(label) # Creating a specific bottom scale label
                        bLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        bLabel.setAlignment(Qt.AlignCenter) # Bottom scale labels will be centered under radio buttons
                        bLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                        fontMetrics = bLabel.fontMetrics() # Gathering information on label size given the chosen font
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", label)
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                        if tempWidth < self._spacing: # Bottom scale labels have to be at least as wide as spacing argument
                            tempWidth = self._spacing

                        if self._topScaleLabels:
                            if labelWidthList[i-1] < tempWidth: # Deciding if top or bottom scale label is wider
                                labelWidthList[i-1] = tempWidth # Setting the maximum width (either top or bottom scale label width)
                            else:
                                tempWidth = labelWidthList[i-1]
                        else:
                            labelWidthList.append(tempWidth)

                        cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                        cellLayout.addWidget(bLabel)
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, self._items+1, i, 1,1, alignment=4)
                        self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter)
                        i=i+1

                '''
                The following part deals with general matrix layout after each cell has been created
                '''

                if self._itemLabels: # Setting all itemLabels to the same width (each side separately)
                    for i in range (self._items):
                        self._likertLayout.itemAtPosition(i+1, self._levels+1).widget().setFixedWidth(maximumRightLabelWidth)
                        self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedWidth(maximumLeftLabelWidth)

                        self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedHeight(labelHeightList[i]+2) # Adjusting 2px for margin
                        self._likertLayout.itemAtPosition(i+1, self._levels+1).widget().setFixedHeight(labelHeightList[i]+2) # Adjusting 2px for margin

                        for j in range (self._levels):
                            self._likertLayout.itemAtPosition(i+1, j+1).widget().setFixedHeight(labelHeightList[i]+2) # Setting height for RadioButtons

                if self._topScaleLabels or self._bottomScaleLabels: # Setting all elements in each column to a uniform width
                    for i in range (self._levels):
                        if self._topScaleLabels:
                            self._likertLayout.itemAtPosition(0,i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for top scale labels

                        for j in range (self._items):
                            self._likertLayout.itemAtPosition(j+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for radio buttons

                        if self._bottomScaleLabels:
                            self._likertLayout.itemAtPosition(self._items+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for bottom scale labels


            elif self._transpose:
                '''
                The following part constructs the likert matrix with transposing. Different items are therefore
                shown in the horizontal axis while different likert levels for each item are shown in the vettical axis.
                
                Caution!
                
                Labels are still generated in the same order as in untransposed LikertMatrix elements, but functionalities
                of item labels and scale labels have been switched. This might be confusing to developers!
                
                
                '''
                # Setting general cell spacing

                self._likertLayout.setVerticalSpacing(0)
                self._likertLayout.setHorizontalSpacing(0)

                labelWidthList = [] # Will be used to determine necessary cell width for each column of the likert matrix
                labelTopHeightList = [] # Will be used to determine necessary cell height for each row of the likert matrix
                labelBottomHeightList = [] # Will be used to determine necessary cell height for each row of the likert matrix

                if self._topScaleLabels: #Top scale labels are shown directly above the first row of radio buttons
                    i = 1
                    for label in self._topScaleLabels: # Each label is processed separately
                        cellFrame = QFrame() # Creating an empty frame for item label

                        cellLayout = QVBoxLayout() # New layout for label cell
                        cellLayout.setSpacing(0)
                        cellLayout.setContentsMargins(2,2,2,2)
                        cellLayout.setAlignment(Qt.AlignRight) # All left item labels will be aligned right

                        lLabel = QLabel(label) # Creating the actual item label using the permutation list in case of shuffle
                        lLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        lLabel.adjustSize() # Update label size for correct layouting

                        fontMetrics = lLabel.fontMetrics() # Gathering font size information
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", label)
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Calculating necessary label size for correct display of itemlabel plus margin

                        if self._itemLabelWidth: # If argument is used tempWidth is overwritten by itemLabelWidth argument
                            tempWidth = self._itemLabelWidth

                        cellFrame.setFixedWidth(tempWidth) # Setting width for label
                        lLabel.setAlignment(Qt.AlignRight) # Left item label text alignment is set to right

                        if maximumLeftLabelWidth < tempWidth: # The following code determines the widest left itemlabel to give all item labels a uniform width
                            maximumLeftLabelWidth = tempWidth

                        cellLayout.addWidget(lLabel) # Adding label to cell frame
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, i, 0, 1, 1, alignment=4)
                        self._likertLayout.setAlignment(cellFrame, Qt.AlignRight|Qt.AlignVCenter) # Left item label frames are aligned right
                        i = i+1

                for i in range (self._items): # Beginning new row for each likert item in matrix
                    vars(self)['buttonGroup_'+str(self._permutation[i])] = QButtonGroup(self._elementQtWidget) # Creating new button group for item using the permutated item list in case of shuffle

                    if self._itemLabels: # Item labels are shown left and right of each likert item in the matrix
                        cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                        if i%2 == 0 and self._tableStriped: # Setting different background color to all odd rows if tableStriped flag is set
                            cellFrame.setStyleSheet('background-color: white;')

                        cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(2,2,2,2) # No margins in cell layout
                        cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for top labels

                        tLabel = QLabel(self._itemLabels[self._permutation[i]*2]) # Creating a specific top scale label
                        tLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        tLabel.setAlignment(Qt.AlignCenter) # Top scale labels will be centered above radio buttons
                        tLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                        fontMetrics = tLabel.fontMetrics() # Gathering information on label size given the chosen font
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[self._permutation[i]*2])
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                        if tempWidth < self._spacing: # Top scale labels have to be at least as wide as spacing argument
                            tempWidth = self._spacing

                        labelWidthList.append(tempWidth)

                        tempHeight = fontMetrics.size(0,temp_label_text).height()+4 # plus margin
                        labelTopHeightList.append(tempHeight)

                        cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                        cellLayout.addWidget(tLabel) # Adding label to cell layout 
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame,0, i+1, 1,1, alignment=4) # Adding top scale label frame to correct cell in first row of likert matrix
                        self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter) # Center alignment for top scale label frames

                    for j in range(self._levels): #Adding Radiobuttons for each sclae level in each likert item
                        cellFrame = QFrame() # New empty frame for each radio button
                        if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                            cellFrame.setStyleSheet('background-color: white;')
                        cellFrame.setFixedWidth(self._spacing) # Radio button frames need to be at leas as wide as spacing argument

                        cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(0,0,0,0) # No margins around cell layout

                        vars()['button_'+str(self._permutation[i])+'_'+str(j)] = QRadioButton() # Creating the actual radio button using permutation list in case of shuffle
                        vars()['button_'+str(self._permutation[i])+'_'+str(j)].setStyleSheet('QRadioButton{width: 0px; height: 0px; padding-left: 6px;} QRadioButton::indicator{width: 15px; height: 15px;}') # Disabling text label in QRadioButton and centering indicator
                        vars()['button_'+str(self._permutation[i])+'_'+str(j)].adjustSize()

                        vars(self)['buttonGroup_'+str(self._permutation[i])].addButton(vars()['button_'+str(self._permutation[i])+'_'+str(j)], j) # Button is added to correct button group using permutation list

                        cellLayout.addWidget(vars()['button_'+str(self._permutation[i])+'_'+str(j)])
                        cellLayout.setAlignment(vars()['button_'+str(self._permutation[i])+'_'+str(j)], Qt.AlignCenter) # Radio buttons in cells are centered
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, j+1, i+1, 1, 1, alignment=4) # Button is added to likert matrix with center alignment


                    if self._itemLabels: # Item labels are shown left and right of each likert item in the matrix
                        cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                        if i%2 == 0 and self._tableStriped: # Setting different background color to all odd rows if tableStriped flag is set
                            cellFrame.setStyleSheet('background-color: white')

                        cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                        cellLayout.setSpacing(0) # No spacing in cell layout
                        cellLayout.setContentsMargins(2,2,2,2) # 2px margins in cell layout
                        cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for bottom labels

                        bLabel = QLabel(self._itemLabels[(self._permutation[i]+1)*2-1]) # Creating a specific bottom scale label
                        bLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        bLabel.setAlignment(Qt.AlignCenter) # Bottom scale labels will be centered under radio buttons
                        bLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                        fontMetrics = bLabel.fontMetrics() # Gathering information on label size given the chosen font
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[(self._permutation[i]+1)*2-1])
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                        if tempWidth < self._spacing: # Bottom scale labels have to be at least as wide as spacing argument
                            tempWidth = self._spacing

                        if labelWidthList[i] < tempWidth: # Deciding if top or bottom scale label is wider
                            labelWidthList[i] = tempWidth # Setting the maximum width (either top or bottom scale label width)
                        else:
                            tempWidth = labelWidthList[i]

                        cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                        tempHeight = fontMetrics.size(0,temp_label_text).height()+4 # plus margin

                        labelBottomHeightList.append(tempHeight)

                        cellLayout.addWidget(bLabel)
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, self._levels+1, i+1, 1,1, alignment=4)
                        self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter)

                if self._bottomScaleLabels:
                    i = 1

                    for label in self._bottomScaleLabels: # Each label is processed separately
                        cellFrame = QFrame() # Creating an empty frame for item label

                        cellLayout = QVBoxLayout() # New layout for label cell
                        cellLayout.setSpacing(0)
                        cellLayout.setContentsMargins(2,2,2,2)
                        cellLayout.setAlignment(Qt.AlignLeft) # Alle right item labels will be aligned left

                        rLabel = QLabel(label) # Creating actual right item label using permutation list in case of shuffle
                        rLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                        rLabel.adjustSize() # Updating label size information for correct layouting

                        fontMetrics = rLabel.fontMetrics() # Gathering font size information
                        #Ignore all html tags in text sizing, except html line breaks
                        temp_label_text = re.sub(r"<br>", "\n", label)
                        temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                        tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Calculating necessary label size for correct display of itemlabel plus margin.

                        if self._itemLabelWidth: # If argument is used tempWidth is overwritten by itemLabelWidth argument
                            tempWidth = self._itemLabelWidth

                        cellFrame.setFixedWidth(tempWidth) # Setting width for label
                        rLabel.setAlignment(Qt.AlignLeft) # Right item label text alignment is set to left

                        if maximumRightLabelWidth < tempWidth: # The following code determines the widest right itemlabel to give all item labels a uniform width
                            maximumRightLabelWidth = tempWidth

                        cellLayout.addWidget(rLabel) # Adding label to cell frame
                        cellFrame.setLayout(cellLayout)

                        self._likertLayout.addWidget(cellFrame, i, self._items+1, 1, 1, alignment=4) # Adding right item label to correct cell in likert matrix
                        self._likertLayout.setAlignment(cellFrame, Qt.AlignLeft|Qt.AlignVCenter) # Right item label frames are aligned left
                        i = i+1


                '''
                The following part deals with general matrix layout after each cell has been created
                '''

                if self._topScaleLabels or self._bottomScaleLabels: # Setting all itemLabels to the same width (each side separately)
                    for i in range (self._levels):
                        if self._bottomScaleLabels:
                            self._likertLayout.itemAtPosition(i+1, self._items+1).widget().setFixedWidth(maximumRightLabelWidth)
                        if self._topScaleLabels:
                            self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedWidth(maximumLeftLabelWidth)


                if self._itemLabels: # Setting all elements in each column to a uniform width
                    for i in range (self._items):
                        if self._itemLabels:
                            self._likertLayout.itemAtPosition(0,i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for top scale labels
                            self._likertLayout.itemAtPosition(0,i+1).widget().setFixedHeight(max(labelTopHeightList)+2) # Adjusting 2px for margin

                        for j in range (self._levels):
                            self._likertLayout.itemAtPosition(j+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for radio buttons

                        if self._itemLabels:
                            self._likertLayout.itemAtPosition(self._levels+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for bottom scale labels
                            self._likertLayout.itemAtPosition(self._levels+1, i+1).widget().setFixedHeight(max(labelBottomHeightList)+2)# Adjusting 2px for margin


            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            #Erstellung des äußeren Containers für ElementWidget und CorrectiveHints   
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.setSpacing(5)
            outerWidgetLayout.addWidget(self._instructionText)
            outerWidgetLayout.addLayout(self._likertLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)

            if self._alignment == 'center':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignHCenter)

            elif self._alignment == 'right':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignRight)

            else:
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignLeft)

            # Erstellung des finalen Widgets
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            for i in range (self._items):
                for j in range(self._levels):
                    if self._input[i] == str(j):
                        vars()['button_'+str(i)+'_'+str(j)].setChecked(True)

        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird
        for i in range (self._items):
            for button in vars(self)['buttonGroup_'+str(i)].buttons():
                button.setEnabled(self.enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()


        return self._elementQtWidget


    @property
    def webWidget(self):

        widget = '<div class="likert-matrix"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize), 'style="width: %spx;"' %self._instructionWidth if self._instructionWidth is not None else "", self._instruction)#Extra Table for instruction

        widget = widget + '<table class="%s %s table" style="width: auto; clear: both; font-size: %spt; margin-bottom: 10px;">' % (alignmentConverter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsizeConverter(self._fontSize))#Beginning Table

        if not self._transpose:
            if self._topScaleLabels:
                widget = widget + '<thead><tr><th></th>' #Beginning row for top scalelabels, adding 1 column for left itemLabels
                for label in self._topScaleLabels:
                    widget = widget + '<th class="pagination-centered containerpagination-centered" style="text-align:center;width: %spx; vertical-align: bottom;">%s</th>' %(self._spacing, label) #Adding top Scalelabels

                widget = widget + "<th></th></tr></thead>" #adding 1 Column for right Itemlabels, ending Row for top Scalelabels

            widget = widget + '<tbody>'
            for i in self._permutation:
                widget = widget + '<tr>' # Beginning new row for item
                if self._itemLabels:
                    widget = widget + '<td style="text-align:right; vertical-align: middle;">%s</td>' % self._itemLabels[i*2] #Adding left itemlabel
                else:
                    widget = widget + '<td></td>'#Placeholder if no itemLabels set

                for j in range(self._levels): #Adding Radiobuttons for each level
                    widget = widget + '<td style="text-align:center; vertical-align: middle; margin: auto auto;"><input type="radio" style="margin: 4px 4px 4px 4px;" name="%s" value="%s" %s %s /></td>' % (self.name+'_'+str(i), j, " checked=\"checked\"" if self._input[i] == str(j) else "", "" if self.enabled else " disabled=\"disabled\"")

                if self._itemLabels:
                    widget = widget + '<td style="text-align:left;vertical-align: middle;">%s</td>' % self._itemLabels[(i+1)*2-1] #Adding right itemlabel
                else:
                    widget = widget + '<td></td>'#Placeholder if no itemLabels set

                widget = widget + '</tr>' #Closing row for item
            widget = widget + '</tbody>'

            if self._bottomScaleLabels:
                widget = widget + '<tfoot><tr><th></th>' #Beginning row for bottom scalelabels, adding 1 column for left itemLabels
                for label in self._bottomScaleLabels:
                    widget = widget + '<th class="pagination-centered containerpagination-centered" style="text-align:center;width: %spx; vertical-align: top;">%s</th>' %(self._spacing,label) #Adding bottom Scalelabels

                widget = widget + "<th></th></tr></tfoot>" #adding 1 Column for right Itemlabels, ending Row for bottom Scalelabels

            widget = widget + "</table>" #Closing table for LikertMatrix

        else: #If transposed is set to True
            if self._itemLabels:
                widget = widget + '<tr><td></td>' #Beginning row for top (left without transpose) itemLabels, adding 1 column for left (top without transpose) scalelabels
                for i in range(len(self._itemLabels)/2):
                    widget = widget + '<td class="pagination-centered containerpagination-centered" style="text-align:center; vertical-align: bottom;">%s</td>' % self._itemLabels[i*2] #Adding top itemLabels

                widget = widget + "<td></td></tr>" #adding 1 Column for right scalelabels, ending Row for top itemLabels  

            for i in range (self._levels):
                widget = widget + '<tr style="height: %spx;">' % self._spacing # Beginning new row for level
                if self._topScaleLabels:
                    widget = widget + '<td class="pagination-right" style="vertical-align: middle;">%s</td>' % self._topScaleLabels[i] #Adding left scalelabel
                else:
                    widget = widget + '<td></td>'#Placeholder if no scalelabels set

                for j in range(self._items): #Adding Radiobuttons for each item
                    widget = widget + '<td class="pagination-centered" style="text-align:center; vertical-align: middle; margin: auto auto;"><input type=\"radio\" style="margin: 4px 4px 4px 4px;" name=\"%s\" value=\"%s\"%s%s /></td>' % (self.name+'_'+str(j), i, " checked=\"checked\"" if self._input[j] == str(i) else "", "" if self.enabled else " disabled=\"disabled\"")

                if self._bottomScaleLabels:
                    widget = widget + '<td class="pagination-left" style="vertical-align: middle;">%s</td>' % self._bottomScaleLabels[i] #Adding right scalelabel
                else:
                    widget = widget + '<td></td>'#Placeholder if no scalelabels set

                widget = widget + '</tr>' #Closing row for level

            if self._itemLabels:
                widget = widget + '<tr><td></td>' #Beginning row for bottom (right without transpose) itemLabels, adding 1 column for left (top without transpose) scalelabels
                for i in range(len(self._itemLabels)/2):
                    widget = widget + '<td class="pagination-centered containerpagination-centered" style="text-align:center; vertical-align: top;">%s</td>' % self._itemLabels[(i+1)*2-1] #Adding bottom itemLabels

                widget = widget + "<td></td></tr>" #adding 1 Column for right scalelabels, ending Row for bottom itemLabels 

            widget = widget + "</table>" #Closing table for LikertMatrix

        if self.correctiveHints:

            widget = widget +  '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize)-1, self.correctiveHints[0])

        widget = widget + "</div>"

        return widget

    def validateData(self):
        super(LikertMatrix, self).validateData()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            for i in range(self._items):
                value = int(self._input[i])
                ret = ret and 0 <= value <= self._levels
            return ret
        except:
            return False

    def setData(self, d):
        if self.enabled:
            if d == 'qt':
                for i in range (self._items):
                    self._input[i] = str(vars(self)['buttonGroup_'+str(i)].checkedId())
            else:
                for i in range(self._items):
                    self._input[i] = d.get(self.name+'_'+str(i), '-1')

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []
        if self._forceInput and reduce(lambda b, val: b or val == '-1', self._input, False):
            return [self.no_input_hint]
        else:
            return super(InputElement, self).correctiveHints


class LikertElement(LikertMatrix):
    def __init__(self, instruction='', levels=7, topScaleLabels=None, bottomScaleLabels=None, itemLabels=None, itemLabelWidth=None, spacing=30, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, transpose=False,  **kwargs):
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
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''
        super(LikertElement, self).__init__(instruction=instruction, items=1, levels=levels, topScaleLabels=topScaleLabels, bottomScaleLabels=bottomScaleLabels, itemLabels=itemLabels, itemLabelWidth=itemLabelWidth, spacing=spacing, noInputCorrectiveHint=noInputCorrectiveHint, tableStriped=False, transpose=transpose, shuffle=False, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

    @property
    def data(self):
        lmData = {}
        lmData.update({self.name: None if int(self._input[0])+1 == 0 else int(self._input[0])+1})
        return lmData



class SingleChoiceElement(LikertElement):
    def __init__(self, instruction='', itemLabels=[], itemLabelWidth=None, itemLabelHeight=None, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, shuffle=False, tableStriped=False, **kwargs):
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
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        kwargs.pop('transpose',None)#Stellt sicher, dass keine ungültigen Argumente verwendet werden
        kwargs.pop('items',None) #Stellt sicher, dass keine ungültigen Argumente verwendet werden

        if len(itemLabels) == 0:
            raise ValueError(u"Es müssen Itemlabels übergeben werden.")

        super(SingleChoiceElement, self).__init__(instruction=instruction, noInputCorrectiveHint=noInputCorrectiveHint, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

        self._permutation = range(len(itemLabels))
        if shuffle:
            random.shuffle(self._permutation)

        self._itemLabelWidth = itemLabelWidth
        self._itemLabelHeight = itemLabelHeight
        self._tableStriped = tableStriped
        self._items = len(itemLabels)
        self._itemLabels = itemLabels
        self._suffle = shuffle

        if settings.debugmode and settings.debug.defaultValues:
            self._input = str(int(self._input[0]))
        elif not self._input == '':
            self._input = str(int(self._input[0]))
            self._defaultSet = True
        else:
            self._input = '-1'

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()

            fontSize = fontsizeConverter(self._fontSize) # Converting fontSize into valid argument

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+12 # +2 for margins. +10 for layout purposes

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting instruction text alignment
            self._instructionText.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight)

            # Creating central likert matrix layout

            self._likertLayout = QGridLayout()
            self._likertLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            self._likertLayout.setHorizontalSpacing(0)
            self._likertLayout.setVerticalSpacing(0)

            maxLabelWidth= 0 # Will be used to determine necessary cell width for each column of the likert matrix

            vars(self)['buttonGroup'] = QButtonGroup(self._elementQtWidget) # Creating new button group for item

            for i in range(self._items): #Adding Radiobuttons for each sclae level in each likert item
                cellFrame = QFrame() # New empty frame for each radio button
                if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                    cellFrame.setStyleSheet('background-color: white;')

                cellFrame.setFixedWidth(30) # Radio button frames need to be at leas as wide as spacing argument

                if self._itemLabelHeight:
                    cellFrame.setFixedHeight(self._itemLabelHeight)

                cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                cellLayout.setSpacing(0) # No spacing in cell layout
                cellLayout.setContentsMargins(0,0,0,0) # No margins around cell layout

                vars()['button_'+str(self._permutation[i])] = QRadioButton() # Creating the actual radio button using permutation list in case of shuffle
                vars()['button_'+str(self._permutation[i])].setStyleSheet('QRadioButton{width: 0px; height: 0px; padding-left: 6px;} QRadioButton::indicator{width: 15px; height: 15px;}') # Disabling text label in QRadioButton
                vars()['button_'+str(self._permutation[i])].adjustSize()

                vars(self)['buttonGroup'].addButton(vars()['button_'+str(self._permutation[i])], self._permutation[i]) # Button is added to correct button group using permutation list

                cellLayout.addWidget(vars()['button_'+str(self._permutation[i])])
                cellLayout.setAlignment(vars()['button_'+str(self._permutation[i])], Qt.AlignHCenter) # Radio buttons in cells are centered
                cellFrame.setLayout(cellLayout)

                self._likertLayout.addWidget(cellFrame, i, 0, 1, 1, alignment=4) # Button is added to likert matrix with center alignment

                ### Creating Labels

                cellFrame = QFrame() # New empty frame for each label
                if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                    cellFrame.setStyleSheet('background-color: white;')

                cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                cellLayout.setSpacing(0) # No spacing in cell layout
                cellLayout.setContentsMargins(2,2,2,2) # No margins around cell layout

                label = QLabel(self._itemLabels[self._permutation[i]]) # Creating a specific top scale label
                label.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                label.setWordWrap(True) #Activates automatic Linebreaks in QLabel
                label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # Top scale labels will be centered above radio buttons
                label.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                fontMetrics = label.fontMetrics() # Gathering information on label size given the chosen font
                #Ignore all html tags in text sizing, except html line breaks
                temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[self._permutation[i]])
                temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                if self._itemLabelWidth: # Top scale labels have to be at least as wide as spacing argument
                    tempWidth = self._itemLabelWidth

                if maxLabelWidth < tempWidth:
                    maxLabelWidth = tempWidth

                cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                if self._itemLabelHeight:
                    cellFrame.setFixedHeight(self._itemLabelHeight)

                cellLayout.addWidget(label) # Adding label to cell layout 
                cellFrame.setLayout(cellLayout)

                self._likertLayout.addWidget(cellFrame, i, 1, 1, 1, alignment=4) # Adding frame to correct cell in first row of likert matrix
                self._likertLayout.setAlignment(cellFrame,Qt.AlignLeft|Qt.AlignVCenter) # Left alignment for label frames

            for i in range (self._items):
                self._likertLayout.itemAtPosition(i,1).widget().setFixedWidth(maxLabelWidth) # Setting column width for top scale labels

            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            #Erstellung des äußeren Containers für ElementWidget und CorrectiveHints   
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.setSpacing(5)
            outerWidgetLayout.addWidget(self._instructionText)
            outerWidgetLayout.addLayout(self._likertLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)

            if self._alignment == 'center':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignHCenter)

            elif self._alignment == 'right':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignRight)

            else:
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignLeft)

            # Erstellung des finalen Widgets
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            for i in range(self._items):
                if self._input == str(i):
                    vars()['button_'+str(i)].setChecked(True)

        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird

        for button in vars(self)['buttonGroup'].buttons():
            button.setEnabled(self.enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()

        return self._elementQtWidget

    @property
    def webWidget(self):

        widget = '<div class="single-choice-element"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize), 'style="width: %spx;"' %self._instructionWidth if self._instructionWidth is not None else "", self._instruction)#Extra Table for instruction

        widget = widget + '<table class="%s %s table" style="width: auto; clear: both; font-size: %spt; margin-bottom: 10px;">' % (alignmentConverter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsizeConverter(self._fontSize))#Beginning Table

        for i in range(self._items): #Adding Radiobuttons for each sclae level in each likert item

            widget = widget + '<tr><td class="pagination-centered" style="vertical-align: middle; margin: auto auto;"><input type=\"radio\" style="margin: 4px 4px 4px 4px;" name=\"%s\" value=\"%s\"%s%s /></td>' % (self.name, self._permutation[i], " checked=\"checked\"" if self._input == str(self._permutation[i]) else "", "" if self.enabled else " disabled=\"disabled\"")

            widget = widget + '<td class="pagination-left" style="vertical-align: middle;" %s>%s</td></tr>' % ('width: '+str(self._itemLabelWidth)+'px;' if self._itemLabelWidth else '',self._itemLabels[self._permutation[i]]) #Adding item label

        widget = widget + "</table>" #Closing table for SingleChoiceElement

        if self.correctiveHints:
            widget = widget +  '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize), self.correctiveHints[0])

        widget = widget + '</div>'

        return widget

    def setData(self, d):
        if self.enabled:
            if d == 'qt':
                self._input = str(vars(self)['buttonGroup'].checkedId())
            else:
                self._input = d.get(self.name, '-1')

    @property
    def data(self):
        d = {self.name: None if int(self._input)+1 == 0 else int(self._input)+1}
        if self._suffle:
            d[self.name + '_permutation'] = [i+1 for i in self._permutation]
        return d

    def validateData(self):
        super(SingleChoiceElement, self).validateData()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            value = int(self._input)
            ret = ret and 0 <= value <= self._levels
            return ret
        except:
            return False

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []
        if self._forceInput and self._input == '-1':
            return [self.no_input_hint]
        else:
            return super(InputElement, self).correctiveHints

class MultipleChoiceElement(LikertElement):
    def __init__(self, instruction='', itemLabels=[], minSelect=None, maxSelect=None, selectHint=None, itemLabelWidth=None, itemLabelHeight=None, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, shuffle=False, tableStriped=False, **kwargs):
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
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        kwargs.pop('transpose',None) #Stellt sicher, dass keine ungültigen Argumente verwendet werden
        kwargs.pop('items',None) #Stellt sicher, dass keine ungültigen Argumente verwendet werden

        default = kwargs.pop('default',None)
        debugString = kwargs.pop('debugString',None)

        if len(itemLabels) == 0:
            raise ValueError(u"Es müssen Itemlabels übergeben werden.")

        super(MultipleChoiceElement, self).__init__(instruction=instruction, noInputCorrectiveHint=noInputCorrectiveHint, instructionWidth=instructionWidth, instructionHeight=instructionHeight, **kwargs)

        self._permutation = range(len(itemLabels))
        if shuffle:
            random.shuffle(self._permutation)

        self._itemLabelWidth = itemLabelWidth
        self._itemLabelHeight = itemLabelHeight
        self._tableStriped = tableStriped
        self._items = len(itemLabels)

        if minSelect and minSelect > self._items:
            raise ValueError('minSelect must be smaller than number of items')

        if maxSelect and maxSelect < 2:
            raise ValueError('maxSelect must be set to 2 or higher')

        self._minSelect = minSelect
        self._maxSelect = maxSelect

        if selectHint:
            self._select_hint = selectHint
        else:
            if minSelect and not maxSelect:
                self._select_hint = u"Bitte wählen Sie mindestens %i Optionen aus" % self._minSelect
            elif maxSelect and not minSelect:
                self._select_hint = u"Bitte wählen Sie höchstens %i Optionen aus" % self._maxSelect
            elif maxSelect and minSelect:
                self._select_hint = u"Bitte wählen Sie mindestens %i und höchstens %i Optionen aus" % (self._minSelect, self._maxSelect)

        if self._minSelect:
            self._noInputCorrectiveHint = self._select_hint

        self._itemLabels = itemLabels
        self._suffle = shuffle

        #default values and debug values have to be implemented with the following workaround resulting from deducing LikertItem

        self._input = ['0' for i in range(len(self._itemLabels))]

        if settings.debugmode and settings.debug.defaultValues:
            if not debugString:
                self._input = settings.debug.get(self.__class__.__name__) #getting default value (True or False)   
            else:
                self._input = settings._config_parser.get('debug', debugString)

            if self._input == True:
                self._input = ['1' for i in range(len(self._itemLabels))]
            else:
                self._input = ['0' for i in range(len(self._itemLabels))]

        if default is not None:
            self._input = default

            if not len(self._input) == len(self._itemLabels):
                raise ValueError('Wrong default data! Default value must be set to a list of %s values containing either "0" or "1"!' %(len(self._itemLabels)))

    @property
    def webWidget(self):

        widget = '<div class="multiple-choice-element"><table class="%s" style="clear: both; font-size: %spt; margin-bottom: 10px;"><tr><td %s>%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize), 'style="width: %spx;"' %self._instructionWidth if self._instructionWidth is not None else "", self._instruction)#Extra Table for instruction

        widget = widget + '<table class="%s %s" style="clear: both; font-size: %spt; line-height: normal; margin-bottom: 10px;">' % (alignmentConverter(self._alignment, 'container'), 'table-striped' if self._tableStriped else '', fontsizeConverter(self._fontSize))#Beginning Table

        for i in range(self._items):
            widget = widget + '<tr style="height: %spx;"><td class="pagination-centered" style="vertical-align: middle; margin: auto auto;"><input type="checkbox" style="vertical-align: middle; margin: 4px 4px 4px 4px;" name="%s" value="%s" %s %s /></td>' % (self._spacing, self.name+'_'+str(self._permutation[i]), 1, " checked=\"checked\"" if self._input[self._permutation[i]] == '1' else "", "" if self.enabled else " disabled=\"disabled\"")
            widget = widget + '<td class="pagination-left" style="vertical-align: middle;">%s</td></tr>' % self._itemLabels[self._permutation[i]]

        widget = widget + '</table>'

        if self.correctiveHints:
            widget = widget +  '<table class="%s" style="clear: both; font-size: %spt;"><tr><td class="corrective-hint" >%s</td></tr></table>' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize), self.correctiveHints[0])

        widget = widget + '</div>'

        return widget

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()

            fontSize = fontsizeConverter(self._fontSize) # Converting fontSize into valid argument

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+12 # +2 for margins. +10 for layout purposes

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting instruction text alignment
            self._instructionText.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight)

            # Creating central likert matrix layout

            self._likertLayout = QGridLayout()
            self._likertLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            self._likertLayout.setHorizontalSpacing(0)
            self._likertLayout.setVerticalSpacing(0)

            maxLabelWidth= 0 # Will be used to determine necessary cell width for each column of the likert matrix

            for i in range(self._items): #Adding Radiobuttons for each sclae level in each likert item
                cellFrame = QFrame() # New empty frame for each radio button
                if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                    cellFrame.setStyleSheet('background-color: white;')

                cellFrame.setFixedWidth(30) # Radio button frames need to be at leas as wide as spacing argument

                if self._itemLabelHeight:
                    cellFrame.setFixedHeight(self._itemLabelHeight)

                cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                cellLayout.setSpacing(0) # No spacing in cell layout
                cellLayout.setContentsMargins(0,0,0,0) # No margins around cell layout

                vars(self)['box_'+str(self._permutation[i])] = QCheckBox() # Creating the actual radio button using permutation list in case of shuffle
                vars(self)['box_'+str(self._permutation[i])].setStyleSheet('QCheckBox{width: 0px; height: 0px; padding-left: 6px;} QCheckBox::indicator{width: 15px; height: 15px;}') # Disabling text label in QRadioButton
                vars(self)['box_'+str(self._permutation[i])].adjustSize()

                cellLayout.addWidget(vars(self)['box_'+str(self._permutation[i])])
                cellLayout.setAlignment(vars(self)['box_'+str(self._permutation[i])], Qt.AlignHCenter) # Radio buttons in cells are centered
                cellFrame.setLayout(cellLayout)

                self._likertLayout.addWidget(cellFrame, i, 0, 1, 1, alignment=4) # Button is added to likert matrix with center alignment

                ### Creating Labels

                cellFrame = QFrame() # New empty frame for each label
                if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                    cellFrame.setStyleSheet('background-color: white;')

                cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                cellLayout.setSpacing(0) # No spacing in cell layout
                cellLayout.setContentsMargins(2,2,2,2) # No margins around cell layout

                label = QLabel(self._itemLabels[self._permutation[i]]) # Creating a specific top scale label
                label.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                label.setWordWrap(True) #Activates automatic Linebreaks in QLabel
                label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # Top scale labels will be centered above radio buttons
                label.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                fontMetrics = label.fontMetrics() # Gathering information on label size given the chosen font
                #Ignore all html tags in text sizing, except html line breaks
                temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[self._permutation[i]])
                temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                if self._itemLabelWidth: # Top scale labels have to be at least as wide as spacing argument
                    tempWidth = self._itemLabelWidth

                if maxLabelWidth < tempWidth:
                    maxLabelWidth = tempWidth

                cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                if self._itemLabelHeight:
                    cellFrame.setFixedHeight(self._itemLabelHeight)

                cellLayout.addWidget(label) # Adding label to cell layout 
                cellFrame.setLayout(cellLayout)

                self._likertLayout.addWidget(cellFrame, i, 1, 1, 1, alignment=4) # Adding frame to correct cell in first row of likert matrix
                self._likertLayout.setAlignment(cellFrame,Qt.AlignLeft|Qt.AlignVCenter) # Left alignment for label frames

            for i in range (self._items):
                self._likertLayout.itemAtPosition(i,1).widget().setFixedWidth(maxLabelWidth) # Setting column width for top scale labels

            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            #Erstellung des äußeren Containers für ElementWidget und CorrectiveHints      
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.setSpacing(5)
            outerWidgetLayout.addWidget(self._instructionText)
            outerWidgetLayout.addLayout(self._likertLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)

            # Einstellen der Elementausrichtung
            if self._alignment == 'center':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignHCenter)
            elif self._alignment == 'right':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignRight)
            else:
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignLeft)

            # Erstellung des finalen Widgets
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            # Setzen des Checkstate (debug mode)

            for i in range(self._items):
                if self._input[self._permutation[i]] == '1':
                    vars(self)['box_'+str(self._permutation[i])].setChecked(True)


        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird
        for i in range(self._items):
            vars(self)['box_'+str(i)].setEnabled(self._enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()

        return self._elementQtWidget

    @property
    def data(self):
        mcData = {}
        for i in range(self._items):
            mcData.update({self.name+'_'+str(i+1): int(self._input[i])})
        if self._suffle:
            mcData[self.name + '_permutation'] = [i + 1 for i in self._permutation]
        return mcData

    def setData(self, d):
        if self.enabled:
            if d == 'qt':
                for i in range (self._items):
                    if vars(self)['box_'+str(i)].isChecked():
                        self._input[i] = '1'
                    else:
                        self._input[i] = '0'
            else:
                for i in range(self._items):
                    self._input[i] = d.get(self.name+'_'+str(i), '0')

    def validateData(self):
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
    def correctiveHints(self):
        if not self.showCorrectiveHints:
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

        return super(InputElement, self).correctiveHints


class LikertListElement(InputElement, WebElementInterface, QtElementInterface):
    def __init__(self, instruction='', levels=7, topScaleLabels=None, bottomScaleLabels = None,
                 itemLabels = [], itemLabelHeight=None, itemLabelWidth=None, itemLabelAlignment='left',
                 tableStriped=False, spacing = 30, shuffle=False, instructionWidth=None,
                 instructionHeight=None, useShortLabels=False, **kwargs):
        '''
        **LikertListElement** displays a likert item with images as labels.
        Instruction is shown above element.

        :param str name: Name of WebLikertImageElement and stored input variable.
        :param str instruction: Instruction to be displayed above likert matrix (can contain html commands).
        :param int levels: Number of scale levels..
        :param int spacing: Sets column width between radio buttons.
        :param str alignment: Alignment of WebLikertImageElement in widget container ('left' as default, 'center', 'right').
        :param str/int font: Fontsize used in WebLikertImageElement ('normal' as default, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as default or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        super(LikertListElement, self).__init__(**kwargs)

        self._instruction = instruction
        self._instructionWidth = instructionWidth
        self._instructionHeight = instructionHeight
        self._levels = levels
        self._topScaleLabels = topScaleLabels
        self._bottomScaleLabels = bottomScaleLabels
        self._itemLabels = itemLabels
        self._itemLabelHeight = itemLabelHeight
        self._itemLabelWidth = itemLabelWidth
        self._itemLabelAlign = itemLabelAlignment
        self._tableStriped = tableStriped
        self._spacing = spacing
        self._defaultSet = False
        self._useShortLabels = useShortLabels

        if spacing < 30:
            raise ValueError(u'Spacing must be greater or equal than 30!')

        if topScaleLabels is not None and not len(topScaleLabels) == self._levels:
            raise ValueError(u"Es müssen keine oder %s OBERE Skalenlabels übergeben werden." % self._levels)

        if bottomScaleLabels is not None and not len(bottomScaleLabels) == self._levels:
            raise ValueError(u"Es müssen keine oder %s UNTERE Skalenlabels übergeben werden." % self._levels)

        self._permutation = range(len(itemLabels))
        if shuffle:
            random.shuffle(self._permutation)

        if settings.debugmode and settings.debug.defaultValues:
            self._input = [str(int(self._input)-1) for i in itemLabels]
        elif not self._input == '':
            self._input = [str(int(self._input)-1) for i in itemLabels]
            self._defaultSet = True
        else:
            self._input = ['-1' for i in itemLabels]

        self._elementQtWidget = None

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
    def canDisplayCorrectiveHintsInline(self):
        return True

    def _short_labels(self):
        l = 6
        rv = []
        for label in self._itemLabels:
            if label != '':
                label = label.replace('.', '')
                words = label.split()
                num = int(round((l / len(words)) + 0.5))
                sl = ''
                for w in words:
                    sl = sl + w[:num]
                rv.append(sl[:l])
            else:
                rv.append('')
        return rv


    @property
    def data(self):
        d = {}
        d[self._name + '_permutation'] = [i+1 for i in self._permutation]
        short_labels = self._short_labels()
        for i in range(len(self._itemLabels)):
            label = self.name+'_'+str(i+1)
            if self._useShortLabels:
                label += '_' + short_labels[i]
            d[label] = int(self._input[i])+1
            if d[label] == 0:
                d[label] = None
        return d

    def setData(self, d):
        if self._enabled:
            if d == 'qt':
                for i in range (len(self._itemLabels)):
                    self._input[i] = str(vars(self)['buttonGroup_'+str(i)].checkedId())
            else:
                for i in range(len(self._itemLabels)):
                    self._input[i] = d.get(self.name+'_'+str(i), '-1')

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()

            fontSize = fontsizeConverter(self._fontSize) # Converting fontSize into valid argument

            #Ignore all html tags in text sizing, except html line breaks
            temp_text = re.sub(r"<br>", "\n", self._instruction)
            temp_text = re.sub(r"<[^<>]*>", "", temp_text)

            # Creating label
            self._instructionText = QLabel(self._instruction)

            self._instructionText.setWordWrap(True) #Activates automatic Linebreaks in QLabel
            self._instructionText.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
            self._instructionText.adjustSize() #Updates label to correct size

            fontMetrics = self._instructionText.fontMetrics()
            tempWidth = fontMetrics.size(0, temp_text).width()

            if tempWidth > self._maximumWidgetWidth:
                tempWidth = self._maximumWidgetWidth

            if self._instructionWidth:
                tempWidth = self._instructionWidth

            self._instructionText.setFixedWidth(tempWidth)

            tempHeight = fontMetrics.boundingRect(0,0, tempWidth, 10000, Qt.TextWordWrap, temp_text).height()+12 # +2 for margins. +10 for layout purposes

            if self._instructionHeight:
                tempHeight = self._instructionHeight

            self._instructionText.setFixedHeight(tempHeight)

            # Setting instruction text alignment
            self._instructionText.setAlignment(Qt.AlignLeft)
            if self._alignment == 'center':
                self._instructionText.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                self._instructionText.setAlignment(Qt.AlignRight)


            #Erstellung des eigentlichen ElementWidget
            self._likertLayout = QGridLayout()
            self._likertLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            self._likertLayout.setHorizontalSpacing(0)
            self._likertLayout.setVerticalSpacing(0)

            labelWidthList = [] # Will be used to determine necessary cell width for each column of the likert matrix
            labelHeightList = [] # Will be used to determine necessary cell height for each row of the likert matrix


            maximumLeftLabelWidth = 0 # Variable will be used to determine uniform width of left item labels

            if self._topScaleLabels: #Top scale labels are shown directly above the first row of radio buttons
                i = 1
                for label in self._topScaleLabels: # Each label is processed separately
                    cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                    cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                    cellLayout.setSpacing(0) # No spacing in cell layout
                    cellLayout.setContentsMargins(2,2,2,2) # No margins in cell layout
                    cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for top labels

                    tLabel = QLabel(label) # Creating a specific top scale label
                    tLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                    tLabel.setAlignment(Qt.AlignCenter) # Top scale labels will be centered above radio buttons
                    tLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                    fontMetrics = tLabel.fontMetrics() # Gathering information on label size given the chosen font
                    #Ignore all html tags in text sizing, except html line breaks
                    temp_label_text = re.sub(r"<br>", "\n", label)
                    temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)


                    tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                    if tempWidth < self._spacing: # Top scale labels have to be at least as wide as spacing argument
                        tempWidth = self._spacing

                    labelWidthList.append(tempWidth)

                    cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                    cellLayout.addWidget(tLabel) # Adding label to cell layout 
                    cellFrame.setLayout(cellLayout)

                    self._likertLayout.addWidget(cellFrame,0, i, 1,1, alignment=4) # Adding top scale label frame to correct cell in first row of likert matrix
                    self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter) # Center alignment for top scale label frames
                    i=i+1

            for i in range (len(self._itemLabels)): # Beginning new row for item
                vars(self)['buttonGroup_'+str(self._permutation[i])] = QButtonGroup(self._elementQtWidget)

                cellFrame = QFrame() # Creating an empty frame for item label
                if i%2 == 0 and self._tableStriped: # Setting different background color to all odd rows if tableStriped flag is set
                    cellFrame.setStyleSheet('background-color: white;')

                cellLayout = QVBoxLayout() # New layout for label cell
                cellLayout.setSpacing(0)
                cellLayout.setContentsMargins(2,2,2,2)

                if self._itemLabelAlign == 'left':
                    cellLayout.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # All left item labels will be aligned
                if self._itemLabelAlign == 'center':
                    cellLayout.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter) # All left item labels will be aligned
                if self._itemLabelAlign == 'right':
                    cellLayout.setAlignment(Qt.AlignRight|Qt.AlignVCenter) # All left item labels will be aligned

                lLabel = QLabel(self._itemLabels[self._permutation[i]]) # Creating the actual item label using the permutation list in case of shuffle
                lLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                lLabel.adjustSize() # Update label size for correct layouting

                fontMetrics = lLabel.fontMetrics() # Gathering font size information
                #Ignore all html tags in text sizing, except html line breaks
                temp_label_text = re.sub(r"<br>", "\n", self._itemLabels[self._permutation[i]])
                temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Calculating necessary label size for correct display of itemlabel plus margin

                if self._itemLabelWidth: # If argument is used tempWidth is overwritten by itemLabelWidth argument
                    tempWidth = self._itemLabelWidth

                cellFrame.setFixedWidth(tempWidth) # Setting width for label

                if maximumLeftLabelWidth < tempWidth: # The following code determines the widest left itemlabel to give all item labels a uniform width
                    maximumLeftLabelWidth = tempWidth

                tempHeight = fontMetrics.size(0,temp_label_text).height()+4 # plus margin

                if self._itemLabelHeight:
                    tempHeight = self._itemLabelHeight

                labelHeightList.append(tempHeight)

                if self._itemLabelAlign == 'left':
                    lLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) # Left item label text alignment is set
                elif self._itemLabelAlign == 'center':
                    lLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter) # Left item label text alignment is set
                elif self._itemLabelAlign == 'right':
                    lLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter) # Left item label text alignment is set

                cellLayout.addWidget(lLabel) # Adding label to cell frame
                cellFrame.setLayout(cellLayout)

                self._likertLayout.addWidget(cellFrame, i+1, 0, 1, 1, alignment=4)
                self._likertLayout.setAlignment(cellFrame, Qt.AlignRight|Qt.AlignVCenter) # Left item label frames are aligned right

                # Creating radio buttons     

                for j in range(self._levels): #Adding Radiobuttons for each scale level in each likert item
                    cellFrame = QFrame() # New empty frame for each radio button

                    if i%2 == 0 and self._tableStriped: # Changing background color in every odd row of likert items if tableStriped argument is used
                        cellFrame.setStyleSheet('background-color: white;')
                    cellFrame.setFixedWidth(self._spacing) # Radio button frames need to be at leas as wide as spacing argument

                    cellLayout = QVBoxLayout() # New Layout for each frame around a radio button
                    cellLayout.setSpacing(0) # No spacing in cell layout
                    cellLayout.setContentsMargins(0,0,0,0) # No margins around cell layout

                    vars()['button_'+str(self._permutation[i])+'_'+str(j)] = QRadioButton() # Creating the actual radio button using permutation list in case of shuffle
                    vars()['button_'+str(self._permutation[i])+'_'+str(j)].setStyleSheet('QRadioButton{width: 0px; height: 0px; padding-left: 6px;} QRadioButton::indicator{width: 15px; height: 15px;}') # Disabling text label in QRadioButton and centering indicator
                    vars()['button_'+str(self._permutation[i])+'_'+str(j)].adjustSize()

                    vars(self)['buttonGroup_'+str(self._permutation[i])].addButton(vars()['button_'+str(self._permutation[i])+'_'+str(j)], j) # Button is added to correct button group using permutation list

                    cellLayout.addWidget(vars()['button_'+str(self._permutation[i])+'_'+str(j)])
                    cellLayout.setAlignment(vars()['button_'+str(self._permutation[i])+'_'+str(j)], Qt.AlignCenter) # Radio buttons in cells are centered
                    cellFrame.setLayout(cellLayout)

                    self._likertLayout.addWidget(cellFrame, i+1, j+1, 1, 1, alignment=4) # Button is added to likert matrix with center alignment
                    self._likertLayout.setAlignment(cellFrame, Qt.AlignCenter) # RadioButtons are being centered


                self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedWidth(maximumLeftLabelWidth)


            if self._bottomScaleLabels:
                i = 1

                for label in self._bottomScaleLabels: # Each label is processed separately
                    cellFrame = QFrame() # Labels are embedded in separate frames which is necessary to color the label background
                    cellLayout = QVBoxLayout() # Cell frames need separate layout to which a label will be added
                    cellLayout.setSpacing(0) # No spacing in cell layout
                    cellLayout.setContentsMargins(2,2,2,2) # No margins in cell layout
                    cellLayout.setAlignment(Qt.AlignHCenter) # Center alignment for bottom labels

                    bLabel = QLabel(label) # Creating a specific bottom scale label
                    bLabel.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % fontSize)
                    bLabel.setAlignment(Qt.AlignCenter) # Bottom scale labels will be centered under radio buttons
                    bLabel.adjustSize() # Calling minimumSizeHint will update label sizeHint, which is needed for correct layouting

                    fontMetrics = bLabel.fontMetrics() # Gathering information on label size given the chosen font
                    #Ignore all html tags in text sizing, except html line breaks
                    temp_label_text = re.sub(r"<br>", "\n", label)
                    temp_label_text = re.sub(r"<[^<>]*>", "", temp_label_text)

                    tempWidth = fontMetrics.size(0,temp_label_text).width()+4 # Width of label plus margin

                    if tempWidth < self._spacing: # Bottom scale labels have to be at least as wide as spacing argument
                        tempWidth = self._spacing

                    if self._topScaleLabels:
                        if labelWidthList[i-1] < tempWidth: # Deciding if top or bottom scale label is wider
                            labelWidthList[i-1] = tempWidth # Setting the maximum width (either top or bottom scale label width)
                        else:
                            tempWidth = labelWidthList[i-1]
                    else:
                        labelWidthList.append(tempWidth)

                    cellFrame.setFixedWidth(tempWidth) # Setting exact size of label

                    cellLayout.addWidget(bLabel)
                    cellFrame.setLayout(cellLayout)

                    self._likertLayout.addWidget(cellFrame, len(self._itemLabels)+1, i, 1,1, alignment=4)
                    self._likertLayout.setAlignment(cellFrame,Qt.AlignCenter)
                    i=i+1


            if self._itemLabels: # Setting all itemLabels to the same width (each side separately)
                for i in range (len(self._itemLabels)):
                    self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedWidth(maximumLeftLabelWidth)

                    self._likertLayout.itemAtPosition(i+1, 0).widget().setFixedHeight(labelHeightList[i]+2) # Adjusting 2px for margin
                    self._likertLayout.itemAtPosition(i+1, self._levels).widget().setFixedHeight(labelHeightList[i]+2) # Adjusting 2px for margin

                    for j in range (self._levels):
                        self._likertLayout.itemAtPosition(i+1, j+1).widget().setFixedHeight(labelHeightList[i]+2) # Setting height for RadioButtons

            if self._topScaleLabels or self._bottomScaleLabels: # Setting all elements in each column to a uniform width
                for i in range (self._levels):
                    if self._topScaleLabels:
                        self._likertLayout.itemAtPosition(0,i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for top scale labels

                    for j in range (len(self._itemLabels)):
                        self._likertLayout.itemAtPosition(j+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for radio buttons

                    if self._bottomScaleLabels:
                        self._likertLayout.itemAtPosition(len(self._itemLabels)+1, i+1).widget().setFixedWidth(labelWidthList[i]) # Setting column width for bottom scale labels



            self._correctiveHint = QLabel('')
            self._correctiveHint.setStyleSheet('color: red; font-family: Arial,Helvetica,sans-serif; font-size: %spt;' % (fontSize-1))

            #Erstellung des äußeren Containers für ElementWidget und CorrectiveHints   
            outerWidgetLayout = QVBoxLayout()
            outerWidgetLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            outerWidgetLayout.setSpacing(5)
            outerWidgetLayout.addWidget(self._instructionText)
            outerWidgetLayout.addLayout(self._likertLayout)
            outerWidgetLayout.addWidget(self._correctiveHint)

            if self._alignment == 'center':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignHCenter)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignHCenter)

            elif self._alignment == 'right':
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignRight)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignRight)

            else:
                outerWidgetLayout.setAlignment(self._instructionText, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._likertLayout, Qt.AlignLeft)
                outerWidgetLayout.setAlignment(self._correctiveHint, Qt.AlignLeft)

            # Erstellung des finalen Widgets
            self._elementQtWidget.setLayout(outerWidgetLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            for i in range (len(self._itemLabels)):
                for j in range(self._levels):
                    if self._input[i] == str(j):
                        vars()['button_'+str(i)+'_'+str(j)].setChecked(True)

        # Generelle Aktualisierung des Widgets, die bei jedem Aufruf durchgeführt wird
        for i in range (len(self._itemLabels)):
            for button in vars(self)['buttonGroup_'+str(i)].buttons():
                button.setEnabled(self.enabled)

        self._correctiveHint.hide()

        if self.correctiveHints:
            self._correctiveHint.setText(self.correctiveHints[0])
            self._correctiveHint.show()

        return self._elementQtWidget

    @property
    def webWidget(self):
        d = {}
        d['fontsize'] = fontsizeConverter(self._fontSize)
        d['contalignment'] = alignmentConverter(self._alignment, 'container')
        d['alignment'] = self._alignment
        d['instruction'] = self._instruction
        d['striped'] = 'table-striped' if self._tableStriped else ''
        d['spacing'] = self._spacing
        d['hints'] = self.correctiveHints
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

    def validateData(self):
        super(LikertListElement, self).validateData()
        try:
            if not self._forceInput or not self._shouldBeShown:
                return True

            ret = True
            for v in self._input:
                ret = ret and 0 <= int(v) < self._levels
            return ret
        except:
            return False

    @property
    def correctiveHints(self):
        if not self.showCorrectiveHints:
            return []
        if self._forceInput and reduce(lambda b, val: b or val == '-1', self._input, False):
            return [self.no_input_hint]
        else:
            return super(LikertListElement, self).correctiveHints




class ImageElement(Element, WebElementInterface, QtElementInterface):
    def __init__(self, path=None, url=None, xSize=None, ySize=None, alt=None, maximizable=False, **kwargs):
        super(ImageElement, self).__init__(**kwargs)

        if not path and not url:
            raise ValueError('path or url must be set in image element')

        if path and not os.path.isabs(path):
            path = os.path.join(settings.general.external_files_dir, path)

        self._path = path
        self._url = url

        self._xSize = xSize
        self._ySize = ySize
        self._alt = alt
        self._image_url = None
        self._elementQtWidget = None
        self._maximizable = maximizable
        self._min_times = []
        self._max_times = []
        if maximizable and settings.experiment.type == 'qt':
            raise RuntimeError('maximizable is not implemented for qt')

    def prepareWebWidget(self):
        if self._image_url is None:
            if self._path:
                self._image_url = self._question._experiment.userInterfaceController.addStaticFile(self._path)
            elif self._url:
                self._image_url = self._url

    @property
    def qtWidget(self):
        if self._elementQtWidget == None:
            # Erstellen des Labels  
            self._imagePixmap = QPixmap(self._path)

            if self._xSize and self._ySize:
                self._imagePixmap = self._imagePixmap.scaled(self._xSize,self._ySize)

            elif self._xSize and not self._ySize:
                self._imagePixmap = self._imagePixmap.scaledToWidth(self._xSize)

            elif self._ySize and not self._xSize:
                self._imagePixmap = self._imagePixmap.scaledToHeight(self._ySize)

            self._imageLabel = QLabel()
            self._imageLabel.setPixmap(self._imagePixmap)

            # Erstellung des eigentlichen Widgets
            imageLayout = QHBoxLayout()
            imageLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            imageLayout.addWidget(self._imageLabel)

            # Einstellen der Elementausrichtung
            if self._alignment == 'center':
                imageLayout.setAlignment(Qt.AlignHCenter)
            elif self._alignment == 'right':
                imageLayout.setAlignment(Qt.AlignRight)
            else:
                imageLayout.setAlignment(Qt.AlignLeft)

            self._elementQtWidget = QWidget()
            self._elementQtWidget.setLayout(imageLayout)

            self._elementQtWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)

        return self._elementQtWidget

    @property
    def webWidget(self):
        html =  '<p class="%s">' % alignmentConverter(self._alignment, 'text')

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
    def cssCode(self):
        return [(10,
        '''
            #overlay-%s {position:absolute;left:0;top:0;min-width:100%%;min-height:100%%;z-index:1 !important;background-color:black;
        ''' % self.name)
        ]

    @property
    def jsCode(self):
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
        return [(10, template.substitute(linkid='link-'+self.name, overlayid='overlay-'+self.name,
            imageid='image-'+self.name, imgurl=self._image_url, maxtimes=self.name+'_max_times',
            mintimes=self.name + '_min_times'))]

    @property
    def data(self):
        if self._maximizable:
            return {self.name + '_max_times': self._max_times, self.name + '_min_times': self._min_times}
        return {}

    def setData(self, d):
        if self.enabled and self._maximizable:
            if d == 'qt':
                raise RuntimeError("maximizable is not implemented for qt")
            else:
                try:
                    self._min_times = json.loads(d.get(self.name + '_min_times', '[]'))
                    self._max_times = json.loads(d.get(self.name + '_max_times', '[]'))
                except:
                    self._min_times = []
                    self._max_times = []

class TableElement(Element, WebElementInterface, QtElementInterface):
    def __init__(self, elements=[], **kwargs):
        super(TableElement, self).__init__(**kwargs)
        self._elements = elements

        self._elementQtWidget = None

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
    def qtWidget(self):
        if self._elementQtWidget == None:
            self._elementQtWidget = QWidget()
            self._elementQtWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)

            rowLayout = QVBoxLayout()
            rowLayout.setContentsMargins(0,0,0,0)
            rowLayout.setSpacing(5)

            for l in self._elements:

                lineLayout = QHBoxLayout()
                lineLayout.setContentsMargins(0,0,0,0)
                lineLayout.setSpacing(5)

                for e in l:
                    if e.shouldBeShown:
                        elementWidget = e.qtWidget
                        lineLayout.addWidget(elementWidget)
                        lineLayout.setAlignment(elementWidget, Qt.AlignLeft)

                        if e.alignment == 'center':
                            self._contentLayout.setAlignment(elementWidget, Qt.AlignHCenter)

                        if e.alignment == 'right':
                            self._contentLayout.setAlignment(elementWidget, Qt.AlignRight)

                rowLayout.addLayout(lineLayout)

                self._elementQtWidget.setLayout(rowLayout)

        return self._elementQtWidget


    def prepareQtWidget(self):
        for e in self.flat_elements:
            e.maximumWidgetWidth = self._question._experiment.userInterfaceController.layout.maximumWidgetWidth
            e.prepareQtWidget()

    @property
    def flat_elements(self):
        return [e for l in self._elements for e in l]

    def addedToQuestion(self, q):
        super(TableElement, self).addedToQuestion(q)
        for e in self.flat_elements:
            e.addedToQuestion(q)

    @property
    def data(self):
        d = {}
        for e in self.flat_elements:
            d.update(e.data)
        return d

    def setData(self, data):
        for e in self.flat_elements:
            e.setData(data)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        for e in self.flat_elements:
            e.enabled = enabled

    @property
    def canDisplayCorrectiveHintsInline(self):
        return reduce(lambda b, e: b and e.canDisplayCorrectiveHintsInline, self.flat_elements, True)

    @property
    def correctiveHints(self):
        return [hint for e in self.flat_elements for hint in e.correctiveHints]


    @property
    def showCorrectiveHints(self):
        return self._showCorrectiveHints

    @showCorrectiveHints.setter
    def showCorrectiveHints(self, b):
        self._showCorrectiveHints = b
        for e in self.flat_elements:
            e.showCorrectiveHints = b

    def validateData(self):
        return reduce(lambda b, e: b and e.validateData(), self.flat_elements, True)

    @property
    def webWidget(self):
        html = '<table class="%s" style="text-align: center; font-size:%spt">' % (alignmentConverter(self._alignment, 'container'), fontsizeConverter(self._fontSize))

        for l in self._elements:
            html = html + '<tr>'
            for e in l:
                html = html + '<td>' + e.webWidget if e.shouldBeShown else '' + '</td>'
            html = html + '</tr>'
        html = html + '</table>'

        return html

    def prepareWebWidget(self):
        for e in self.flat_elements:
            e.prepareWebWidget()

    @property
    def cssCode(self):
        return [code for e in self.flat_elements for code in e.cssCode]

    @property
    def cssURLs(self):
        return [url for e in self.flat_elements for url in e.cssURLs]

    @property
    def jsCode(self):
        return [code for e in self.flat_elements for code in e.jsCode]

    @property
    def jsURLs(self):
        return [url for e in self.flat_elements for url in e.jsURLs]

class WebSliderElement(InputElement, WebElementInterface):
    def __init__(self, instruction='', sliderWidth = 200, min=0, max=100, step=1, noInputCorrectiveHint=None, instructionWidth=None, instructionHeight=None, itemLabels=None, topLabel=None, bottomLabel=None, **kwargs):
        '''
        **TextSliderElement*** returns a slider bar.

        :param str name: Name of TextEntryElement and stored input variable.
        :param str instruction: Instruction to be displayed with line edit field (can contain html commands).
        :param int instructionWidth: Minimum horizontal size of instruction label (can be used for layouting purposes).
        :param int instructionHeight: Minimum vertical size of instruction label (can be used for layouting purposes).
        :param str alignment: Alignment of TextEntryElement in widget container ('left' as standard, 'center', 'right').
        :param str/int fontSize: Font size used in TextEntryElement ('normal' as standard, 'big', 'huge', or int value setting fontsize in pt).
        :param bool forceInput: Sets user input to be mandatory (False as standard or True).
        :param str noInputCorrectiveHint: Hint to be displayed if forceInput set to True and no user input registered.
        '''

        #TODO: Required image files from jquery-ui are missing! Widget will not be displayed correctly, but works nonetheless.
        super(WebSliderElement, self).__init__(noInputCorrectiveHint = noInputCorrectiveHint, **kwargs)

        self._instructionWidth = instructionWidth
        self._instructionHeight = instructionHeight
        self._instruction = instruction
        self._sliderWidth = sliderWidth
        self._min = min
        self._max = max
        self._step = step

        if itemLabels is not None and not len(itemLabels) == 2:
            raise ValueError(u"Es müssen keine oder 2 Itemlabels übergeben werden.")
        self._itemLabels = itemLabels
        self._topLabel = topLabel
        self._bottomLabel = bottomLabel

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
                    <td valign="bottom"><div style="width: {{ sliderWidth }}px; margin-left: 15px; margin-right: 15px; margin-top: 5px; margin-bottom: 5px;" name="{{ name }}" value="{{ input }}" {% if disabled %}disabled="disabled"{% endif %}></div></td>
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
    def webWidget(self):

        d = {}
        d['alignment'] = alignmentConverter(self._alignment, 'container')
        d['fontsize'] = fontsizeConverter(self._fontSize)
        d['width'] = self._instructionWidth
        d['sliderWidth'] = self._sliderWidth
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
        if self.correctiveHints:
            d['corrective_hint'] = self.correctiveHints[0]
        return self._template.render(d)


    @property
    def canDisplayCorrectiveHintsInline(self):
        return True

    def validateData(self):
        super(WebSliderElement, self).validateData()

        if not self._shouldBeShown:
            return True

        if self._forceInput and self._input == '':
            return False

        return True

    def setData(self, d):
        if self.enabled:
            self._input = d.get(self.name, '')

        if self._input == 'None':
            self._input = ''
    
    
class WebAudioElement(Element, WebElementInterface):
    def __init__(self, wavURL= None, wavPath=None, oggURL= None, oggPath=None, mp3URL=None, mp3Path=None, controls=True, autoplay=False, loop=False, **kwargs):
        '''
        TODO: Add docstring
        '''
        super(WebAudioElement, self).__init__(**kwargs)
        if wavPath is not None and not os.path.isabs(wavPath):
            wavPath = os.path.join(settings.general.external_files_dir, wavPath)
        if oggPath is not None and not os.path.isabs(oggPath):
            oggPath = os.path.join(settings.general.external_files_dir, oggPath)
        if mp3Path is not None and not os.path.isabs(mp3Path):
            mp3Path = os.path.join(settings.general.external_files_dir, mp3Path)

        self._wavPath = wavPath
        self._oggPath = oggPath
        self._mp3Path = mp3Path

        self._wav_audio_url = wavURL
        self._ogg_audio_url = oggURL
        self._mp3_audio_url = mp3URL

        self._controls = controls
        self._autoplay = autoplay
        self._loop = loop

        if self._wavPath is None and self._oggPath is None and self._mp3Path is None and self._wav_audio_url is None and self._ogg_audio_url is None and self._mp3_audio_url is None:
            raise(AlfredError('Keine Audioquelle definiert!'))

    def prepareWebWidget(self):

        if self._wav_audio_url is None and self._wavPath is not None:
            self._wav_audio_url = self._question._experiment.userInterfaceController.addStaticFile(self._wavPath)

        if self._ogg_audio_url is None and self._oggPath is not None:
            self._ogg_audio_url = self._question._experiment.userInterfaceController.addStaticFile(self._oggPath)

        if self._mp3_audio_url is None and self._mp3Path is not None:
            self._mp3_audio_url = self._question._experiment.userInterfaceController.addStaticFile(self._mp3Path)

    @property
    def webWidget(self):
        widget = '<div class="audio-element"><p class="%s"><audio %s %s %s><source src="%s" type="audio/mp3"><source src="%s" type="audio/ogg"><source src="%s" type="audio/wav">Your browser does not support the audio element</audio></p></div>' % (alignmentConverter(self._alignment, 'both'), 'controls' if self._controls else '', 'autoplay' if self._autoplay else '', 'loop' if self._loop else '',self._mp3_audio_url, self._ogg_audio_url, self._wav_audio_url)

        return widget


class WebVideoElement(Element, WebElementInterface):
    def __init__(self, width=None, height=None, mp4URL= None, mp4Path=None, oggURL= None, oggPath=None, webMURL=None, webMPath=None, controls=True, autoplay=False, loop=False, **kwargs):
        '''
        TODO: Add docstring
        '''
        super(WebVideoElement, self).__init__(**kwargs)
        if mp4Path is not None and not os.path.isabs(mp4Path):
            mp4Path = os.path.join(settings.general.external_files_dir, mp4Path)
        if oggPath is not None and not os.path.isabs(oggPath):
            oggPath = os.path.join(settings.general.external_files_dir, oggPath)
        if webMPath is not None and not os.path.isabs(webMPath):
            webMPath = os.path.join(settings.general.external_files_dir, webMPath)

        self._mp4Path = mp4Path
        self._oggPath = oggPath
        self._webMPath = webMPath

        self._mp4_video_url = mp4URL
        self._ogg_video_url = oggURL
        self._webM_video_url = webMURL

        self._controls = controls
        self._autoplay = autoplay
        self._loop = loop
        self._width = width
        self._height = height

        if self._mp4Path is None and self._oggPath is None and self._webMPath is None and self._mp4_video_url is None and self._ogg_video_url is None and self._webM_video_url is None:
            raise(AlfredError('Keine Videoquelle definiert!'))

    def prepareWebWidget(self):

        if self._mp4_video_url is None and self._mp4Path is not None:
            self._mp4_video_url = self._question._experiment.userInterfaceController.addStaticFile(self._mp4Path)

        if self._ogg_video_url is None and self._oggPath is not None:
            self._ogg_video_url = self._question._experiment.userInterfaceController.addStaticFile(self._oggPath)

        if self._webM_video_url is None and self._webMPath is not None:
            self._webM_video_url = self._question._experiment.userInterfaceController.addStaticFile(self._webMPath)

    @property
    def webWidget(self):
        widget = '<div class="video-element"><p class="%s"><video %s %s %s %s %s><source src="%s" type="video/mp4"><source src="%s" type="video/ogg"><source src="%s" type="video/webM">Your browser does not support the video element</audio></p></div>' % (alignmentConverter(self._alignment, 'both'), 'width="'+str(self._width)+'"' if self._width else '', 'height="'+str(self._height)+'"' if self._height else '', 'controls' if self._controls else '', 'autoplay' if self._autoplay else '', 'loop' if self._loop else '',self._mp4_video_url, self._ogg_video_url, self._webM_video_url)

        return widget

class ExperimenterMessages(TableElement):
    def prepareWebWidget(self):
        self._elements = []
        messages = self._question._experiment.experimenterMessageManager.getMessages()

        for message in messages:
            output = ''

            if not message.title == '':
                output = output + '<strong>' + message.title + '</strong> - '

            output = output + message.msg

            message.level = '' if message.level == 'warning' else 'alert-' + message.level

            message_element = TextElement('<div class="alert '+message.level+'"><button type="button" class="close" data-dismiss="alert">&times;</button>'+output+' </div>')

            message_element.addedToQuestion(self._question)

            self._elements.append([message_element])

        super(ExperimenterMessages, self).prepareWebWidget()

    def prepareQtWidget(self):

        # First we need to delete old qtWidget

        if self._elementQtWidget:
            oldQtWidget = self._elementQtWidget
            oldQtWidget.hide()
            oldQtWidget.setParent(None)
            self._elementQtWidget = None #This will result in new rendering of widget every time it is shown.

        self._elements = []
        messages = self._question._experiment.experimenterMessageManager.getMessages()

        for message in messages:
            output = ''

            if not message.title == '':
                output = output + '<strong>' + message.title + '</strong> - '

            output = output + message.msg

            message_element = TextElement(output)

            message_element.addedToQuestion(self._question)

            if message.level == 'warning':
                bg_color = '#FCF8E3'
                text_color = '#C09853'

            elif message.level == 'error':
                bg_color = '#F2DEDE'
                text_color = '#B94A48'

            elif message.level == 'info':
                bg_color = '#D9EDF7'
                text_color = '#3A87AD'

            elif message.level == 'success':
                bg_color = '#DFF0D8'
                text_color = '#468847'

            # Warning Background: #FCF8E3 / Warning Color: #C09853
            # Error Background: #F2DEDE / Error Color: #B94A48
            # Info Background: #D9EDF7 / Info Color: #3A87AD
            # Success Background: #DFF0D8 / Success Color: #468847

            message_element.maximumWidgetWidth = self._question._experiment.userInterfaceController.layout.maximumWidgetWidth

            message_element.qtWidget.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: 12pt; background-color: '+bg_color+'; color: '+text_color+'; padding: 3px; border-width: 1px; border-style: solid; border-radius: 4px; border-color: '+text_color+';')

            self._elements.append([message_element])

        super(ExperimenterMessages, self).prepareQtWidget()

class WebExitEnabler(Element, WebElementInterface):
    @property
    def webWidget(self):
        widget = "<script>$(document).ready(function(){glob_unbind_leaving();});</script>"

        return widget

