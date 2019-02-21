# -*- coding:utf-8 -*-
u'''
Experiment script using Alfred - A library for rapid experiment development.

Experiment name: Exemplary name

Experiment version: 0.1

Experiment author: ctreffe <mail@adress.com>

Description: Here you should give a short description of your experiment and it's purpose
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

my_global_variable = ''


def my_function():
    pass

#################################
# - Section 3: Custom classes - #
#################################


class MyClass(object):
    pass


########################################
# - Section 4: Experiment generation - #
########################################

class Script(object):
    def generate_experiment(self):
        exp = Experiment('qt-wk', 'myExperiment', '0.1')

        # exp._userInterfaceController.changeLayout(GoeWebLayout())

        myQ = CompositeQuestion(elements=[
            TextElement("Hello W11orld!!!"),
            TextEntryElement("as"),
            # ImageElement("test.jpg"),
            # ImageElement("test.png"),
        ]
        )

        myQuestion = CompositeQuestion(
            elements=[
                TextElement(text='some text'),
            ]
        )

        myQuestion2 = CompositeQuestion(
            elements=[
                TextElement(text='some text'),
            ]
        )
        myGroup = SegmentedQG()
        myGroup.appendItems(myQ, myQuestion2, myQuestion
                            )

        exp.questionController.appendItem(myGroup)

        return exp


generate_experiment = Script().generate_experiment
