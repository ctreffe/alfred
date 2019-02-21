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
import alfred.settings as settings

from alfred import Experiment

#################################################
# - Section 2: Global variables and functions - #
#################################################
text01 = TextElement()

#################################
# - Section 3: Custom classes - #
#################################


########################################
# - Section 4: Experiment generation - #
########################################

class Script(object):
    def generate_experiment(self):
        exp = Experiment('web', 'myExperiment', '0.1')

        page01 = CompositeQuestion(title="Page 01")
        page02 = CompositeQuestion(title="Page 02")
        page03 = CompositeQuestion(title="Page 03")
        page04 = CompositeQuestion(title="Page 04")
        page05 = CompositeQuestion(title="Page 05")

        main = QuestionGroup()
        group01 = HeadOpenQG()
        group01.appendItems(page01, page02)

        group02 = SegmentedQG()
        group02.appendItems(page03, page04, page05)

        main.appendItems(group01, group02)

        exp.questionController.appendItem(myGroup)

        return exp


generate_experiment = Script().generate_experiment
