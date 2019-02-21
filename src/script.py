# -*- coding:utf-8 -*-
u'''
Experiment script using Alfred - A library for rapid experiment development.

Experiment name: Full Functionality Overview

Experiment version: 0.1

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
text01 = TextElement(text="Normal Centered Text", name="text1", alignment="center")
text02 = TextElement(text="Big Left Text", name="text2", alignment="left", fontSize="big")
text03 = TextElement(text="Small Right Text", name="text3", alignment="right", fontSize=8)

# DataElement
data01 = DataElement(variable=10, name="data01")


textentry01 = TextEntryElement(instruction="Geben Sie hier beliebigen Text ein.")
textentry02 = TextEntryElement(instruction="Hier müssen Sie Text eingeben.", forceInput=True)


#################################
# - Section 3: Custom classes - #
#################################


########################################
# - Section 4: Experiment generation - #
########################################

class Script(object):
    def generate_experiment(self):
        exp = Experiment('qt-wk', 'myExperiment', '0.1')

        page01 = CompositeQuestion(title="Page 01")
        page02 = CompositeQuestion(title="Page 02")
        page03 = CompositeQuestion(title="Page 03")
        page04 = CompositeQuestion(title="Page 04")
        page05 = CompositeQuestion(title="Page 05")

        page01.addElements(text01, text02, text03, hline01, pbar01, data01)
        page02.addElements()

        main = QuestionGroup()
        # main = SegmentedQG()
        group01 = HeadOpenQG()
        group01.appendItems(page01, page02)

        group02 = SegmentedQG()
        group02.appendItems(page03, page04, page05)

        main.appendItems(group01, group02)

        exp.questionController.appendItem(main)

        return exp


generate_experiment = Script().generate_experiment
