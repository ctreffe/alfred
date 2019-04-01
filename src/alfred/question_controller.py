# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

In *question_controller* wird die Basisklasse *QuestionController* bereit gestellt.
'''
from __future__ import absolute_import
from builtins import object
from alfred._core import Direction

from .questionGroup import QuestionGroup
from .question import CompositeQuestion, WebCompositeQuestion
from .element import TextElement, WebExitEnabler


class QuestionController(object):
    '''
    | QuestionController stellt die obersten Fragengruppen des Experiments (*rootQuestionGroup* und *finishedQuestionGroup*)
    | bereit und ermöglicht den Zugriff auf auf deren Methoden und Attribute.
    '''

    def __init__(self, experiment):
        self._experiment = experiment

        self._rootQuestionGroup = QuestionGroup(tag='rootQuestionGroup')
        self._rootQuestionGroup.added_to_experiment(experiment)

        self._finishedQuestionGroup = QuestionGroup(tag='finishedQuestionGroup', title='Experiment beendet')

        if self._experiment.type == 'qt':
            self._finishedQuestionGroup.append_item(CompositeQuestion(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.')]))
        else:
            self._finishedQuestionGroup.append_item(WebCompositeQuestion(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.'), WebExitEnabler()]))

        self._finishedQuestionGroup.added_to_experiment(experiment)

        self._finished = False
        self._finishedQuestionAdded = False

    def __getattr__(self, name):
        '''
        Die Funktion reicht die aufgerufenen Attribute und Methoden an die oberen Fragengruppen weiter.

        Achtung: Nur bei Items in der switchList wird zwischen rootQuestionGroup und finishedQuestionGroup unterschieden.
        '''
        switchList = ['current_question', 'current_title', 'current_subtitle', 'current_status_text', 'should_be_shown',
                      'jumplist', 'can_move_backward', 'can_move_forward', 'move_backward', 'move_forward', 'move_to_first',
                      'move_to_last', 'move_to_position']
        try:
            if name in switchList:
                if self._finished:
                    return self._finishedQuestionGroup.__getattribute__(name)
                else:
                    return self._rootQuestionGroup.__getattribute__(name)
            else:
                return self._rootQuestionGroup.__getattribute__(name)
        except AttributeError as e:
            raise e
            # raise AttributeError("'%s' has no Attribute '%s'" % (self.__class__.__name__, name))

    def append_item_to_finish_question_group(self, item):
        '''
        :param item: Element vom Typ Question oder QuestionGroup

        .. todo:: Ist diese Funktion überhaupt nötig, wenn die finishedQuestionGroup in init bereits erstellt wird?
        '''
        if not self._finishedQuestionAdded:
            self._finishedQuestionAdded = True
            self._finishedQuestionGroup = QuestionGroup(tag='finishedQuestionGroup')
            self._finishedQuestionGroup.added_to_experiment(self._experiment)
        self._finishedQuestionGroup.append_item(item)

    def added_to_experiment(self, exp):
        '''
        Ersetzt __getattr___ und erreicht so sowohl die rootQuestionGroup als auch die finishedQuestionGroup

        :param exp: Objekt vom Typ Experiment
        '''
        self._experiment = exp
        self._rootQuestionGroup.added_to_experiment(exp)
        self._finishedQuestionGroup.added_to_experiment(exp)

    def change_to_finished_group(self):
        self._finished = True
        self._rootQuestionGroup.leave(Direction.FORWARD)
        self._finishedQuestionGroup.enter()
        self._finishedQuestionGroup.move_to_first()
        self._experiment.user_interface_controller.layout.finish_disabled = True
