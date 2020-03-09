# -*- coding:utf-8 -*-

#################################
# - Section 1: Module imports - #
#################################

import alfred.section as sec
import alfred.element as elm
from alfred import Experiment
from alfred.page import Page
from alfred.helpmates import parse_xml_to_dict


#################################################
# - Section 2: Global variables and functions - #
#################################################

#################################
# - Section 3: Page definitions - #
#################################

class Welcome(Page):

    def on_showing(self):
        el = elm.TextElement(self.values.welcome_text)
        self.append(el)

########################################
# - Section 4: Experiment generation - #
########################################

def generate_experiment(self, custom_settings=None):
    exp = Experiment(custom_settings=custom_settings)

    # --- Page 1 --- #
    page01 = Welcome(title="Hello, world!", values={"welcome_text": "test"})

    # Sections
    main = sec.SegmentedSection()
    main.append_items(page01)

    # Initialize and fill experiment
    exp.append(main)

    return exp
