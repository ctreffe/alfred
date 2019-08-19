# -*- coding:utf-8 -*-
'''
Experiment script using Alfred - A library for rapid experiment development.

Experiment author: Johannes Brachem <jobrachem@posteo.de>

Description: This is a basic template for an alfred experiment.
'''


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
EXP_TYPE = "web"
EXP_NAME = "template"
EXP_VERSION = "0.1"
EXP_AUTHOR_MAIL = "your@email.com"

#################################
# - Section 3: Custom classes - #
#################################

########################################
# - Section 4: Experiment generation - #
########################################


class Script(object):

    def generate_experiment(self):
        exp = Experiment(EXP_TYPE, EXP_NAME, EXP_VERSION, EXP_AUTHOR_MAIL)

        # --- Page 1 --- #
        # -------------------------------------- #

        page01 = WebCompositePage(title="Hello, world!")

        # ----------------------------------------------- #
        # Initialize Sections
        main = SegmentedSection()

        # ----------------------------------------------- #
        # Fill Sections

        # ----------------------------------------------- #
        # Append to main section #
        # ----------------------------------------------- #

        main.append_items(page01)

        # Append Main Group to Experiment
        exp.append(main)

        return exp


generate_experiment = Script().generate_experiment
