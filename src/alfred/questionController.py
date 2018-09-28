# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

In *questionController* wird die Basisklasse *QuestionController* bereit gestellt.
'''
from alfred._core import Direction

from questionGroup import QuestionGroup
from question import CompositeQuestion, WebCompositeQuestion
from element import TextElement, WebExitEnabler

class QuestionController(object):
    '''
    | QuestionController stellt die obersten Fragengruppen des Experiments (*rootQuestionGroup* und *finishedQuestionGroup*) 
    | bereit und ermöglicht den Zugriff auf auf deren Methoden und Attribute.
    '''
    def __init__(self, experiment):
        self._experiment = experiment

        self._rootQuestionGroup = QuestionGroup(tag='rootQuestionGroup')
        self._rootQuestionGroup.addedToExperiment(experiment)

        self._finishedQuestionGroup = QuestionGroup(tag='finishedQuestionGroup', title='Experiment beendet')

        if self._experiment.type == 'qt':
            self._finishedQuestionGroup.appendItem(CompositeQuestion(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.')]))
        else:
            self._finishedQuestionGroup.appendItem(WebCompositeQuestion(elements=[TextElement(u'Das Experiment ist nun beendet. Vielen Dank für die Teilnahme.'), WebExitEnabler()]))
        
        self._finishedQuestionGroup.addedToExperiment(experiment)

        self._finished = False
        self._finishedQuestionAdded = False

    def __getattr__(self, name):
        '''
        Die Funktion reicht die aufgerufenen Attribute und Methoden an die oberen Fragengruppen weiter.
        
        Achtung: Nur bei Items in der switchList wird zwischen rootQuestionGroup und finishedQuestionGroup unterschieden. 
        '''
        switchList = ['currentQuestion', 'currentTitle', 'currentSubtitle', 'currentStatustext', 'shouldBeShown',\
                'jumplist', 'canMoveBackward', 'canMoveForward', 'moveBackward', 'moveForward', 'moveToFirst',\
                'moveToLast', 'moveToPosition']
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
            #raise AttributeError("'%s' has no Attribute '%s'" % (self.__class__.__name__, name))

    def appendItemToFinishQuestionGroup(self, item):
        '''
        :param item: Element vom Typ Question oder QuestionGroup
        
        .. todo:: Ist diese Funktion überhaupt nötig, wenn die finishedQuestionGroup in init bereits erstellt wird?
        '''
        if not self._finishedQuestionAdded:
            self._finishedQuestionAdded = True
            self._finishedQuestionGroup = QuestionGroup(tag='finishedQuestionGroup')
            self._finishedQuestionGroup.addedToExperiment(self._experiment)
        self._finishedQuestionGroup.appendItem(item)

    def addedToExperiment(self, exp):
        '''
        Ersetzt __getattr___ und erreicht so sowohl die rootQuestionGroup als auch die finishedQuestionGroup
        
        :param exp: Objekt vom Typ Experiment
        '''
        self._experiment = exp
        self._rootQuestionGroup.addedToExperiment(exp)
        self._finishedQuestionGroup.addedToExperiment(exp)

    def changeToFinishedGroup(self):
        self._finished = True
        self._rootQuestionGroup.leave(Direction.FORWARD)
        self._finishedQuestionGroup.enter()
        self._finishedQuestionGroup.moveToFirst()
        self._experiment.userInterfaceController.layout.finishDisabled = True
        
        
