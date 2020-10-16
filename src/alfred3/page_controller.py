# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

In *page_controller* wird die Basisklasse *PageController* bereit gestellt.
"""
from __future__ import absolute_import
from builtins import object
from ._core import Direction

from .section import Section
from .page import CompositePage, WebCompositePage, PageCore
from .element import TextElement, WebExitEnabler
from . import alfredlog


class PageController(object):
    """
    | PageController stellt die obersten Fragengruppen des Experiments (*rootSection* und *finishedSection*)
    | bereit und ermöglicht den Zugriff auf auf deren Methoden und Attribute.
    """

    def __init__(self, experiment):
        self._experiment = experiment

        self._rootSection = Section(tag="rootSection")
        self._rootSection.added_to_experiment(experiment)

        self._finishedSection = Section(tag="finishedSection", title="Experiment beendet")

        final_page = WebCompositePage(tag="finalPage")
        final_page += TextElement("Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.")
        final_page += WebExitEnabler()
        self._finishedSection += final_page

        self._finishedSection.added_to_experiment(experiment)

        self._finished = False
        self._finishedPageAdded = False
        loggername = self.prepare_logger_name()
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__, queue_logger=loggername)

    def __getattr__(self, name):
        """
        Die Funktion reicht die aufgerufenen Attribute und Methoden an die oberen Fragengruppen weiter.

        Achtung: Nur bei Items in der switch_list wird zwischen rootSection und finishedSection unterschieden.
        """
        switch_list = [
            "append",
            "current_page",
            "current_title",
            "current_subtitle",
            "current_status_text",
            "should_be_shown",
            "jumplist",
            "can_move_backward",
            "can_move_forward",
            "move_backward",
            "move_forward",
            "move_to_first",
            "move_to_last",
            "move_to_position",
        ]
        try:
            if name in switch_list:
                if self._finished:
                    return self._finishedSection.__getattribute__(name)
                else:
                    return self._rootSection.__getattribute__(name)
            else:
                return self._rootSection.__getattribute__(name)
        except AttributeError as e:
            raise e
            # raise AttributeError("'%s' has no Attribute '%s'" % (self.__class__.__name__, name))

    def append_item_to_finish_section(self, item):
        """
        :param item: Element vom Typ Page oder Section

        .. todo:: Ist diese Funktion überhaupt nötig, wenn die finishedSection in init bereits erstellt wird?
        """
        if not self._finishedPageAdded:
            self._finishedPageAdded = True
            self._finishedSection = Section(tag="finishedSection")
            self._finishedSection.added_to_experiment(self._experiment)
        self._finishedSection.append(item)

    def added_to_experiment(self, exp):
        """
        Ersetzt __getattr___ und erreicht so sowohl die rootSection als auch die finishedSection

        :param exp: Objekt vom Typ Experiment
        """
        self._experiment = exp
        self._rootSection.added_to_experiment(exp)
        self._finishedSection.added_to_experiment(exp)

    def change_to_finished_section(self):
        self._finished = True
        self._rootSection.leave(Direction.FORWARD)
        self._finishedSection.enter()
        self._finishedSection.move_to_first()
        self._experiment.user_interface_controller.layout.finish_disabled = True

    def change_to_finished_group(self):
        # TODO: Remove in next major update
        self.log.warning(
            "PageController.change_to_finished_group() is deprecated. Use PageController.change_to_finished_section() instead."
        )
        self.change_to_finished_section()

    def pages(self):
        out = []
        for member in self.page_list:
            if isinstance(member, Section):
                out += member.only_pages
            elif isinstance(member, PageCore):
                out.append(member)
        return out

    def prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self._experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        return ".".join(name)
