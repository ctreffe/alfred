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

########################################
# - Section 4: Experiment generation - #
########################################


def generate_experiment(self):
    exp = Experiment()

    # --- Page 1 --- #
    page01 = WebCompositePage(title="Hello, world!")
    el = TextElement("test")
    page01.append(el)

    # Sections
    main = SegmentedSection()
    main.append_items(page01)

    # Initialize and fill experiment
    
    exp.append(main)

    return exp
