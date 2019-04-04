# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

In *question_controller* wird die Basisklasse *PageController* bereit gestellt.
'''
from __future__ import absolute_import
from builtins import object
from alfred._core import Direction

from .section import PageGroup
from .question import CompositePage, WebCompositePage
from .element import TextElement, WebExitEnabler


class PageController(object):
    '''
    | PageController stellt die obersten Fragengruppen des Experiments (*root_section* und *finished_section*)
    | bereit und ermöglicht den Zugriff auf auf deren Methoden und Attribute.
    '''

    def __init__(self, experiment):
        self._experiment = experiment

        self._rootSection = PageGroup(tag='root_section')
        self._rootSection.added_to_experiment(experiment)

        self._finished_section = PageGroup(tag='finished_section', title='Experiment beendet')

        if self._experiment.type == 'qt':
            self._finished_section.append_item(CompositePage(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.')]))
        else:
            self._finished_section.append_item(WebCompositePage(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.'), WebExitEnabler()]))

        self._finished_section.added_to_experiment(experiment)

        self._finished = False
        self._finished_page_added = False

    def __getattr__(self, name):
        '''
        Die Funktion reicht die aufgerufenen Attribute und Methoden an die oberen Fragengruppen weiter.

        Achtung: Nur bei Items in der switch_list wird zwischen root_section und finished_section unterschieden.
        '''
        switch_list = ['current_question', 'current_title', 'current_subtitle', 'current_status_text', 'should_be_shown',
                      'jumplist', 'can_move_backward', 'can_move_forward', 'move_backward', 'move_forward', 'move_to_first',
                      'move_to_last', 'move_to_position']
        try:
            if name in switch_list:
                if self._finished:
                    return self._finished_section.__getattribute__(name)
                else:
                    return self._rootSection.__getattribute__(name)
            else:
                return self._rootSection.__getattribute__(name)
        except AttributeError as e:
            raise e
            # raise AttributeError("'%s' has no Attribute '%s'" % (self.__class__.__name__, name))

    def append_item_to_finish_question_group(self, item):
        '''
        :param item: Element vom Typ Page oder PageGroup

        .. todo:: Ist diese Funktion überhaupt nötig, wenn die finished_section in init bereits erstellt wird?
        '''
        if not self._finished_page_added:
            self._finished_page_added = True
            self._finished_section = PageGroup(tag='finished_section')
            self._finished_section.added_to_experiment(self._experiment)
        self._finished_section.append_item(item)

    def added_to_experiment(self, exp):
        '''
        Ersetzt __getattr___ und erreicht so sowohl die root_section als auch die finished_section

        :param exp: Objekt vom Typ Experiment
        '''
        self._experiment = exp
        self._rootSection.added_to_experiment(exp)
        self._finished_section.added_to_experiment(exp)

    def change_to_finished_group(self):
        self._finished = True
        self._rootSection.leave(Direction.FORWARD)
        self._finished_section.enter()
        self._finished_section.move_to_first()
        self._experiment.user_interface_controller.layout.finish_disabled = True
