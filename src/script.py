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
exp_name = "Full Functionality Overview"
exp_version = "0.1"

#################################
# - Section 3: Custom classes - #
#################################

##########################################
# - Section 4: Define Content Elements - #
##########################################

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
data01 = DataElement(variable=10, name="data01")

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

# RegEntryElement
regentry01 = RegEntryElement(
    name="regentry01",
    instruction="Enter an E-Mail adress",
    alignment="right",
    fontSize="big",
    regEx="[^@]+@[^\.]+\..+",
    default="invalid input",
    forceInput=True,
    matchHint="Please check your input again.",
    noInputCorrectiveHint="You need to enter something.",
    debugString="regentry01_debug"
)

# NumberEntryElement

###########################################
# - Section 5: Define Pages & Structure - #
###########################################

# Initialize Pages
page10 = CompositeQuestion(title="Page 1")
page20 = CompositeQuestion(title="Page 2")
page30 = CompositeQuestion(title="Page 3")
page40 = CompositeQuestion(title="Page 4")
page50 = CompositeQuestion(title="Page 5")

# Fill Pages
page10.addElements(text01, text02, text03, hline01, pbar01, data01)
page20.addElements(textentry01, textentry02, textarea01, textarea02)
page30.addElements(regentry01)

# Initialize Groups
main = SegmentedQG()
group10 = HeadOpenQG()
group20 = SegmentedQG()

# Fill Groups
group10.appendItems(page10, page20)
group20.appendItems(page30, page40, page50)

# Append to main group
main.appendItems(group10, group20)

########################################
# - Section 6: Experiment generation - #
########################################

# Todo: Section 6 in die run.py schieben?


class Script(object):

    def __init__(self, exp_type, exp_name, exp_version, main_pagegroup):
        self.exp_type = exp_type
        self.exp_name = exp_name
        self.exp_version = exp_version
        self.main_pagegroup = main_pagegroup

    def generate_experiment(self):
        exp = Experiment(self.exp_type, self.exp_name, self.exp_version)

        # Append Main Group to Experiment
        exp.questionController.appendItem(self.main_pagegroup)

        return exp


generate_experiment = Script(
    exp_type=exp_type,
    exp_name=exp_name,
    exp_version=exp_version,
    main_pagegroup=main).generate_experiment
