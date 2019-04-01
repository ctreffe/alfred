# -*- coding:utf-8 -*-
'''
Experiment script using Alfred - A library for rapid experiment development.

Experiment author: Johannes Brachem <jobrachem@posteo.de>

Description: This experiment serves to showcase and test Alfred's full functionality.
'''


#################################
# - Section 1: Module imports - #
#################################

from alfred.question import *
from alfred.questionGroup import *
from alfred.element import *
from alfred.layout import *
from alfred.helpmates import *

from alfred import Experiment

#################################################
# - Section 2: Global variables and functions - #
#################################################
exp_type = "qt-wk"
exp_name = "TEST2"
exp_version = "0.3"
exp_author_mail = "jobrachem@posteo.de"

#################################
# - Section 3: Custom classes - #
#################################


class DynamicPage(CompositePage):

    def onShowingWidget(self):
        num01 = self._experiment.dataManager.findExperimentDataByUid('page30')['numberentry01']
        num02 = self._experiment.dataManager.findExperimentDataByUid('page30')['numberentry02']

        input_sum = num01 + num02

        print("number 1:", num01)
        print("number 2:", num02)
        print("sum:", input_sum)
        print("test")

        dynamic_text01 = TextElement(
            name="dynamic_text01",
            text="Input 1: {}<br>Input 2: {}<br>Sum: {}".format(num01, num02, input_sum)
        )

        text01 = self._experiment.dataManager.findExperimentDataByUid('page20')['textentry01']

        dynamic_text02 = TextElement(
            name="dynamic_text02",
            text="Input: {}".format(text01)
        )

        # addAdditionalData and getAdditionalDataByKey test
        self._experiment.dataManager.addAdditionalData("test", 3)
        num03 = self._experiment.dataManager.getAdditionalDataByKey("test")
        dynamic_text03 = TextElement(text="DataManager Test: {}".format(num03))

        self.addElements(dynamic_text01, dynamic_text02, dynamic_text03)


##########################################
# - Section 4: Define Content Elements - #
##########################################

# --- Page 1 --- #
# -------------------------------------- #

# HorizontalLine
hline01 = HorizontalLine(name="hline1", strength=4, color="red")


# ProgressBar
pbar01 = ProgressBar(
    name="pbar",                    # name of the element
    barRange=(0, 99),               # tuple with range of values
    barValue=30,                    # current value of progress, can be changed at any time
    barWidth=300,                   # width of bar
    instruction="Progress Bar",     # text next to bar
    fontSize="big",                 # fontsize
    alignment="center"              # alignment of bar
)

# TextElement
text01 = TextElement(text="Normal Centered Text. Umlaut test: Äöüéû", name="text1", alignment="center")
text02 = TextElement(text="Big Left Text", name="text2", alignment="left", fontSize="big")
text03 = TextElement(text="Small Right Text", name="text3", alignment="right", fontSize=8)

# DataElement
data01 = DataElement(
    variable=10,        # stores the value 10 under the name "data01"
    name="data01"
)

data02 = DataElement(
    variable=23,
    name="data02"
)

# --- Page 2 --- #
# -------------------------------------- #

# TextEntryElement
textentry01 = TextEntryElement(
    instruction="Enter some text.",
    name="textentry01",
    alignment="center",                 # "left", "right"
    fontSize=14,                        # Also possible: "normal", "big", "huge"
    default="Default",
    noInputCorrectiveHint="Please enter something",
    forceInput=True,
    debugString="textentry01_debug"
)

textentry02 = TextEntryElement(instruction="Enter some text.",
                               name="textentry02",
                               noInputCorrectiveHint="Please enter something",
                               forceInput=True
                               )

# TextAreaElement
textarea01 = TextAreaElement(
    instruction="Enter some more text.",
    name="textarea01",
    alignment="right",
    fontSize=16,
    xSize=450,              # horizontal size in pixels
    ySize=300,              # vertical size in pixels
    default="Default",
    forceInput=True,
    noInputCorrectiveHint="Please enter something",
    debugString="textarea01_debug"
)

textarea02 = TextAreaElement(
    instruction="Enter even more text.",
    name="textarea02",
    forceInput=True,
    noInputCorrectiveHint="Please, oh please. You need to enter something.",
)

# --- Page 3 --- #
# -------------------------------------- #

# RegEntryElement
regentry01 = RegEntryElement(
    name="regentry01",
    instruction="Enter an E-Mail adress",
    alignment="right",
    fontSize="big",
    regEx=r"[^@]+@[^\.]+\..+",       # very basic regex for email
    default="invalid input",
    forceInput=True,
    matchHint="Please check your input again.",
    noInputCorrectiveHint="You need to enter something.",
    debugString="regentry01_debug"
)

# NumberEntryElement
numberentry01 = NumberEntryElement(
    name="numberentry01",
    instruction="Enter a number",
    alignment="center",
    fontSize=14,
    decimals=3,
    # min=1.3,
    # max=3.7,
    default=None,
    forceInput=True,
    matchHint="Input not valid.",   # Standard match hint can be altered in config.conf
    noInputCorrectiveHint="Please enter something.",
    debugString="numberentry01_debug"
)

# NumberEntryElement
numberentry02 = NumberEntryElement(
    name="numberentry02",
    instruction="Enter a number",
    alignment="center",
    fontSize="normal",
    decimals=0,
    # min=1.3,
    # max=3.7,
    default=None,
    forceInput=True,
    matchHint="Input not valid.",   # Standard match hint can be altered in config.conf
    noInputCorrectiveHint="Please enter something.",
    debugString="numberentry02_debug"
)


# PasswordElement
password01 = PasswordElement(
    name="password01",
    instruction="Enter any password",
    alignment="left",
    fontSize="normal",
    password="friend",
    default="Speak friend and enter.",
    forceInput=True,
    noInputCorrectiveHint="Speak friend and enter.",
    debugString="password01_debug",
    wrong_password_hint="Speak friend and enter. (wrong_password_hint)"
)

# --- Page 4 --- #
# -------------------------------------- #

# LikertMatrix
likertmatrix01 = LikertMatrix(
    name="likertmatrix01",
    instruction="Enter <b>something</b>",
    alignment="left",       # this is the default
    fontSize="normal",      # this is the default
    levels=5,               # default: 7
    items=3,                # default: 4
    default=4,              # default: None
    itemLabels=[
        "item 1, left", "item 1, right",
        "item 2, left", "item 2, right",
        "item 3, left", "item 3, right"
    ],
    topScaleLabels=["level 1", "level 2", "level 3", "level 4", "level 5"],
    bottomScaleLabels=["level 1", "level 2", "level 3", "level 4", "level 5"],
    transpose=False,        # this is the default
    tableStriped=True,
    shuffle=False,          # this is the default
    itemLabelWidth=4,       # default: None
    spacing=45,             # default: 30
    forceInput=True,        # default: True
    noInputCorrectiveHint="Please enter something.",     # default: None
    debugString="likertmatrix01_debug"
)

likertmatrix02 = LikertMatrix(
    name="likertmatrix02",
    instruction="Enter <b>something</b>",
    alignment="left",       # this is the default
    fontSize="normal",      # this is the default
    levels=5,               # default: 7
    items=3,                # default: 4
    default=None,           # default: None
    itemLabels=[
        "item 1, left", "item 1, right",
        "item 2, left", "item 2, right",
        "item 3, left", "item 3, right"
    ],
    topScaleLabels=["level 1", "level 2", "level 3", "level 4", "level 5"],
    bottomScaleLabels=["level 1", "level 2", "level 3", "level 4", "level 5"],
    transpose=True,
    tableStriped=False,     # this is the default
    shuffle=True,
    itemLabelWidth=None,    # default: None
    spacing=30,             # default: 30
    forceInput=False,      # default: True
    noInputCorrectiveHint="Please enter something.",     # default: None
    debugString="likertmatrix02_debug"
)


# LikertElement
likertelement01 = LikertElement(
    name="likertelement01",
    instruction="Enter something",
    alignment="left",   # this is the default
    fontSize=14,        # default: "normal"
    levels=7,           # this is the default
    default=None,       # this is the default
    itemLabels=["left label", "right label"],
    topScaleLabels=[
        "level 1", "level 2", "level 3", "level 4",
        "level 5", "level 6", "level 7"],
    bottomScaleLabels=[
        "level 1", "level 2", "level 3", "level 4",
        "level 5", "level 6", "level 7"],
    transpose=False,    # default: False
    itemLabelWidth=10,  # default: None
    spacing=40,         # default: 30
    forceInput=True,    # default: True
    noInputCorrectiveHint="Please enter something",
    debugString="likertelement01_debugg"
)

# SingleChoiceElement
singlechoice01 = SingleChoiceElement(
    name="singlechoice01",
    instruction="Enter something",
    alignment="right",
    fontSize=7,
    default=3,
    tableStriped=True,
    itemLabels=["Choice 1", "Choice 2", "Choice 3"],
    itemLabelWidth=None,    # default: None
    itemLabelHeight=None,   # default: None
    shuffle=True,           # default: False
    forceInput=False,       # default: True
    noInputCorrectiveHint="Please enter something",
    debugString="singlechoice01_debug"
)

# MultipleChoiceElement
multiplechoice01 = MultipleChoiceElement(
    name="multiplechoice01",
    instruction="Enter something",
    alignment="center",         # default: "left"
    fontSize="normal",          # default: "normal"
    default=["0", "0", "0"],    # default: None
    tableStriped=True,          # default: False
    itemLabels=["Choice 1", "Choice 2", "Choice 3"],
    itemLabelWidth=None,        # default: None
    itemLabelHeight=None,       # default: None
    shuffle=False,              # default: False
    forceInput=False,           # default: True
    noInputCorrectiveHint="Please enter something",
    debugString="multiplechoice01_debug"
)

# LikertListElement
likertlist01 = LikertListElement(
    name="likertlist01",
    instruction="Enter something",
    alignment="center",         # default: "left"
    fontSize="normal",          # default: "normal"
    default=4,                  # default: None
    tableStriped=False,         # default: False
    levels=5,                   # default: 7
    itemLabels=["1", "2", "3", "4", "5"],
    itemLabelAlignment="right",     # default: "left"
    topScaleLabels=None,            # default: None
    bottomScaleLabels=None,         # default: None
    spacing=30,                     # default: 30
    shuffle=False,                  # default: False
    forceInput=False,               # default: True
    noInputCorrectiveHint="Please enter something",
    debugString="likertlist01_debug"
)

# --- Page 5 --- #
# -------------------------------------- #

# ImageElement
image01 = ImageElement(
    name="image01",
    path="./test.png",
    xSize=350,                      # default: None
    ySize=350,                      # default: None
    alignment="center",             # default: "left"
    alt="Alternative Description",  # web experiments only
    maximizable=True                # web experiments only
)

# TableElement

textentry03 = TextEntryElement(
    instruction="Enter some text.",
    name="textentry01",
    alignment="center",
    fontSize="normal",
    default="Default",
    noInputCorrectiveHint="Please enter something",
    forceInput=True,
    debugString="textentry02_debug"
)

textentry04 = TextEntryElement(
    instruction="Enter some text.",
    name="textentry01",
    alignment="center",
    fontSize="normal",
    default="Default",
    noInputCorrectiveHint="Please enter something",
    forceInput=True,
    debugString="textentry02_debug"
)

textentry05 = TextEntryElement(
    instruction="Enter some text.",
    name="textentry01",
    alignment="center",
    fontSize="normal",
    default="Default",
    noInputCorrectiveHint="Please enter something",
    forceInput=True,
    debugString="textentry04_debug"
)

table01 = TableElement(
    name="table01",
    alignment="center",
    elements=[
        [textentry03, textentry04, textentry05]
    ]
)

###########################################
# - Section 5a: Looped Pages - #
###########################################

loopgroup = PageGroup()

for i in range(4):
    page_num = i + 1
    page = CompositePage(
        title="Looped Page {number}".format(number=page_num),
        uid="page{number}".format(number=page_num)
    )

    text = TextElement(
        name="text_{number}".format(number=page_num),
        text="Looped Text Number {number}".format(number=page_num),
        alignment="center"
    )

    page.addElements(text)

    loopgroup.appendItems(page)


############################################
# - Section 5b: Define Pages & Structure - #
############################################

# ----------------------------------------------- #
# Static Pages
page10 = CompositePage(title="Page 1", uid="page10")
page20 = CompositePage(title="Page 2", uid="page20")
page30 = CompositePage(title="Page 3", uid="page30")
page40 = CompositePage(title="Page 4", uid="page40")
page50 = CompositePage(title="Page 5", uid="page50")

# ----------------------------------------------- #
# Dynamic Pages
page60 = DynamicPage(title="Dynamic Page (Page 6)", uid="page60")

# ----------------------------------------------- #
# Fill Pages
page10.addElements(text01, text02, text03, hline01, pbar01, data01, data02)
page20.addElements(textentry01, textentry02, textarea01, textarea02)
page30.addElements(
    regentry01,
    numberentry01,
    numberentry02,
    password01
)
page40.addElements(
    likertelement01,
    likertmatrix01,
    likertmatrix02,
    singlechoice01,
    multiplechoice01
)
page50.addElements(image01, table01)


# ----------------------------------------------- #
# Initialize Groups
main = SegmentedSection()
group10 = HeadOpenSection()
group20 = SegmentedSection()

# ----------------------------------------------- #
# Fill Groups
group10.appendItems(page10, page20)
group20.appendItems(
    page30,
    page40, page50, page60
)

# ----------------------------------------------- #
# Append to main group #
# ----------------------------------------------- #
# Don't forget to add your question groups made up of loop-generated questions
main.appendItems(
    group10,
    group20,
    loopgroup
)

########################################
# - Section 6: Experiment generation - #
########################################

# Todo: Section 6 in die run.py schieben?


class Script(object):

    def __init__(self, exp_type, exp_name, exp_version, exp_author_mail, main_pagegroup):
        self.exp_type = exp_type
        self.exp_name = exp_name
        self.exp_version = exp_version
        self.exp_author_mail = exp_author_mail
        self.main_pagegroup = main_pagegroup

    def generate_experiment(self):
        exp = Experiment(self.exp_type, self.exp_name, self.exp_version, self.exp_author_mail)

        # Append Main Group to Experiment
        exp.questionController.appendItem(self.main_pagegroup)

        return exp


script = Script(
    exp_type=exp_type,
    exp_name=exp_name,
    exp_version=exp_version,
    exp_author_mail=exp_author_mail,
    main_pagegroup=main)
