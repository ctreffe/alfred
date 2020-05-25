"""A minimalistic 'Hello, World' alfred3 experiment."""

from alfred3 import Experiment
from alfred3.page import Page
import alfred3.section as sec
import alfred3.element as elm


class Welcome(Page):
    def on_showing(self):
        text = elm.TextElement("Hello, Alfred!")
        self.append(text)


def generate_experiment(self, config=None):
    exp = Experiment(config=config)

    welcome = Welcome(title="Hello, World!")

    main = sec.Section()
    main.append(welcome)

    exp.append(main)
    return exp
