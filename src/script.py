# -*- coding:utf-8 -*-

#################################
# - Section 1: Module imports - #
#################################

from alfred.page import WebCompositePage
from alfred.section import SegmentedSection
# from alfred.element import
# from alfred.layout import *
# from alfred.helpmates import *

from alfred import Experiment, run

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

    # --- Sections --- #
    main = SegmentedSection()
    main.append(page01)

    # Append main section to experiment
    exp.page_controller.append(main)

    return exp


run(generate_experiment)
