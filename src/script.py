# -*- coding:utf-8 -*-

#################################
# - Section 1: Module imports - #
#################################

from alfred.page import *
from alfred.section import *
from alfred.element import *
from alfred.layout import *
from alfred.helpmates import *
from alfred import Experiment

#################################################
# - Section 2: Global variables and functions - #
#################################################

#################################
# - Section 3: Custom classes - #
#################################

class Welcome(Page):

    def on_showing_widget(self):
        el = TextElement(self.values.lol)
        self.append(el)

########################################
# - Section 4: Experiment generation - #
########################################


def generate_experiment(self):
    exp = Experiment()

    # --- Page 1 --- #
    page01 = Welcome(title="Hello, world!", values={"lol": "test"})

    # Sections
    main = SegmentedSection()
    main.append_items(page01)

    # Initialize and fill experiment
    
    exp.append(main)

    return exp
