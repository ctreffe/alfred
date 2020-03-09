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

    def on_showing(self):
        el = TextElement(self.values.test)
        self.append(el)

########################################
# - Section 4: Experiment generation - #
########################################


def generate_experiment(self, custom_settings=None):
    exp = Experiment(custom_settings=custom_settings)

    # --- Page 1 --- #
    page01 = Welcome(title="Hello, world!", values={"test": "test"})

    # Sections
    main = SegmentedSection()
    main.append_items(page01)

    # Initialize and fill experiment
    
    exp.append(main)

    return exp
