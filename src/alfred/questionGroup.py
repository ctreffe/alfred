# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
'''
from __future__ import absolute_import

from builtins import str
from builtins import range
from . import alfredlog
from functools import reduce
logger = alfredlog.getLogger(__name__)

from ._core import PageCore, Direction
from .question import Page, HeadOpenSectionCantClose
from .exceptions import MoveError
from random import shuffle


class PageGroup(PageCore):

    def __init__(self, **kwargs):
        super(PageGroup, self).__init__(**kwargs)

        self._questionList = []
        self._currentQuestionIndex = 0
        self._shouldBeShown = True

    def __str__(self):
        s = "PageGroup (tag = " + self.tag + ", questions:[" + str(self._questionList) + "]"
        return s

    @property
    def questionList(self):
        return self._questionList

    @property
    def data(self):
        data = super(PageGroup, self).data
        data['subtreeData'] = []
        for qCore in self._questionList:
            data['subtreeData'].append(qCore.data)

        return data

    @property
    def currentQuestion(self):
        return self._questionList[self._currentQuestionIndex].currentQuestion if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) else self._questionList[self._currentQuestionIndex]

    @property
    def currentTitle(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].currentTitle is not None:
            return self._questionList[self._currentQuestionIndex].currentTitle

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].title is not None:
            return self._questionList[self._currentQuestionIndex].title

        return self.title

    @property
    def currentSubtitle(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].currentSubtitle is not None:
            return self._questionList[self._currentQuestionIndex].currentSubtitle

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].subtitle is not None:
            return self._questionList[self._currentQuestionIndex].subtitle

        return self.subtitle

    @property
    def currentStatustext(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].currentStatustext is not None:
            return self._questionList[self._currentQuestionIndex].currentStatustext

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].statustext is not None:
            return self._questionList[self._currentQuestionIndex].statustext

        return self.statustext

    @PageCore.shouldBeShown.getter
    def shouldBeShown(self):
        '''return true wenn shouldBeShown nicht auf False gesetzt wurde und mindestens eine Frage angezeigt werden will'''
        return super(PageGroup, self).shouldBeShown and reduce(lambda b, qCore: b or qCore.shouldBeShown, self._questionList, False)

    def allowLeaving(self, direction):
        return self._questionList[self._currentQuestionIndex].allowLeaving(direction)

    def enter(self):
        logger.debug(u"Entering PageGroup %s" % self.tag, self._experiment)
        if isinstance(self._coreQuestionAtIndex, PageGroup):
            self._coreQuestionAtIndex.enter()

    def leave(self, direction):
        assert(self.allowLeaving(direction))
        if isinstance(self._coreQuestionAtIndex, PageGroup):
            self._coreQuestionAtIndex.leave(direction)

        logger.debug(u"Leaving PageGroup %s in direction %s" % (self.tag, Direction.to_str(direction)), self._experiment)

    @property
    def jumplist(self):
        # return value: [([0,1], 'JumpText', coreQuestion), ([1], 'JumpText', coreQuestion), ...]

        jumplist = []
        if self.isJumpable:
            jumplist = [([], self.jumptext, self)]

        for i in range(0, len(self._questionList)):
            if isinstance(self._questionList[i], PageGroup):
                for jumpItem in self._questionList[i].jumplist:
                    assert len(jumpItem) == 3
                    jumpItem[0].reverse()
                    jumpItem[0].append(i)
                    jumpItem[0].reverse()
                    jumplist.append(jumpItem)
            elif isinstance(self._questionList[i], Page) and self._questionList[i].isJumpable:
                jumplist.append(([i], self._questionList[i].jumptext, self._questionList[i]))

        return jumplist

    def randomize(self, deep=False):
        self.generateUnsetTagsInSubtree()
        shuffle(self._questionList)

        if deep:
            for item in self._questionList:
                if isinstance(item, PageGroup):
                    item.randomize(True)

    def addedToExperiment(self, exp):
        self._experiment = exp

        for question in self._questionList:
            question.addedToExperiment(self._experiment)

    def appendItem(self, item):
        if not isinstance(item, PageCore):
            raise TypeError("question must be an instance of PageCore")

        self._questionList.append(item)
        item.addedToQuestionGroup(self)

        if self._experiment is not None:
            item.addedToExperiment(self._experiment)

        self.generateUnsetTagsInSubtree()

    def appendItems(self, *items):
        for item in items:
            self.appendItem(item)

    def generateUnsetTagsInSubtree(self):
        for i in range(0, len(self._questionList)):
            if self._questionList[i].tag is None:
                self._questionList[i].tag = str(i + 1)

            if isinstance(self._questionList[i], PageGroup):
                self._questionList[i].generateUnsetTagsInSubtree()

    @property
    def canMoveBackward(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].canMoveBackward:
            return True

        return reduce(lambda b, qCore: b or qCore.shouldBeShown, self._questionList[:self._currentQuestionIndex], False)

    @property
    def canMoveForward(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].canMoveForward:
            return True

        return reduce(lambda b, qCore: b or qCore.shouldBeShown, self._questionList[self._currentQuestionIndex + 1:], False)

    def moveForward(self):
        # test if moving is possible and leaving is allowed
        if not (self.canMoveForward and self.allowLeaving(Direction.FORWARD)):
            raise MoveError()

        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) \
                and self._questionList[self._currentQuestionIndex].canMoveForward:
            self._questionList[self._currentQuestionIndex].moveForward()

        else:
            # if currentQuestion is QG: call leave
            if isinstance(self._coreQuestionAtIndex, PageGroup):
                self._coreQuestionAtIndex.leave(Direction.FORWARD)
            for index in range(self._currentQuestionIndex + 1, len(self._questionList)):
                if self._questionList[index].shouldBeShown:
                    self._currentQuestionIndex = index
                    if isinstance(self._questionList[index], PageGroup):
                        self._questionList[index].moveToFirst()
                        self._coreQuestionAtIndex.enter()
                    break

    def moveBackward(self):
        if not (self.canMoveBackward and self.allowLeaving(Direction.BACKWARD)):
            raise MoveError()

        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) \
                and self._questionList[self._currentQuestionIndex].canMoveBackward:
            self._questionList[self._currentQuestionIndex].moveBackward()

        else:
            # if currentQuestion is QG: call leave
            if isinstance(self._coreQuestionAtIndex, PageGroup):
                self._coreQuestionAtIndex.leave(Direction.BACKWARD)
            for index in range(self._currentQuestionIndex - 1, -1, -1):
                if self._questionList[index].shouldBeShown:
                    self._currentQuestionIndex = index
                    if isinstance(self._questionList[index], PageGroup):
                        self._questionList[index].moveToLast()
                        self._coreQuestionAtIndex.enter()
                    break

    def moveToFirst(self):
        logger.debug(u"QG %s: move to first" % self.tag, self._experiment)
        if not self.allowLeaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._coreQuestionAtIndex, PageGroup):
            self._coreQuestionAtIndex.leave(Direction.JUMP)
        self._currentQuestionIndex = 0
        if self._questionList[0].shouldBeShown:
            if isinstance(self._questionList[0], PageGroup):
                self._coreQuestionAtIndex.enter()
                self._questionList[0].moveToFirst()
        else:
            self.moveForward()

    def moveToLast(self):
        logger.debug(u"QG %s: move to last" % self.tag, self._experiment)
        if not self.allowLeaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._coreQuestionAtIndex, PageGroup):
            self._coreQuestionAtIndex.leave(Direction.JUMP)
        self._currentQuestionIndex = len(self._questionList) - 1
        if self._questionList[self._currentQuestionIndex].shouldBeShown:
            if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
                self._coreQuestionAtIndex.enter()
                self._questionList[0].moveToLast()
        else:
            self.moveBackward()

    def moveToPosition(self, posList):
        if not self.allowLeaving(Direction.JUMP):
            raise MoveError()

        if not isinstance(posList, list) or len(posList) == 0 or not reduce(lambda b, item: b and isinstance(item, int), posList, True):
            raise TypeError("posList must be an list of int with at least one item")

        if not 0 <= posList[0] < len(self._questionList):
            raise MoveError("posList enthaelt eine falsche postionsanganbe.")

        if not self._questionList[posList[0]].shouldBeShown:
            raise MoveError("Die Angegebene Position kann nicht angezeigt werden")

        if isinstance(self._questionList[posList[0]], Page) and 1 < len(posList):
            raise MoveError("posList spezifiziert genauer als moeglich.")

        if isinstance(self._coreQuestionAtIndex, PageGroup):
            self._coreQuestionAtIndex.leave(Direction.JUMP)

        self._currentQuestionIndex = posList[0]
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
            self._coreQuestionAtIndex.enter()
            if len(posList) == 1:
                self._questionList[self._currentQuestionIndex].moveToFirst()
            else:
                self._questionList[self._currentQuestionIndex].moveToPosition(posList[1:])

    @property
    def _coreQuestionAtIndex(self):
        return self._questionList[self._currentQuestionIndex]


class HeadOpenSection(PageGroup):
    def __init__(self, **kwargs):
        super(HeadOpenSection, self).__init__(**kwargs)
        self._maxQuestionIndex = 0

    @property
    def maxQuestionIndex(self):
        return self._maxQuestionIndex

    def allowLeaving(self, direction):
        if direction != Direction.FORWARD:
            return super(HeadOpenSection, self).allowLeaving(direction)

        # direction is Direction.FORWARD

        if isinstance(self._coreQuestionAtIndex, Page):
            HeadOpenSection._setShowCorrectiveHints(self._coreQuestionAtIndex, True)
            return self._coreQuestionAtIndex.allowClosing and super(HeadOpenSection, self).allowLeaving(direction)
        else:  # currentCoreQuestion is Group
            if not self._coreQuestionAtIndex.canMoveForward:
                HeadOpenSection._setShowCorrectiveHints(self._coreQuestionAtIndex, True)
                return HeadOpenSection._allowClosingAllChildQuestions(self._coreQuestionAtIndex) and super(HeadOpenSection, self).allowLeaving(direction)
            else:
                return super(HeadOpenSection, self).allowLeaving(direction)

    @property
    def canMoveForward(self):
        # wenn die aktuelle Fragengruppe oder Frage nicht geschlossen werden
        # kann, return true. Dann kann die HeadOpenSection darauf reagieren und die
        # Frage nochmal mit den corrective Hints anzeigen.
        if isinstance(self._coreQuestionAtIndex, PageGroup) and \
                not self._coreQuestionAtIndex.canMoveForward and \
                not HeadOpenSection._allowClosingAllChildQuestions(self._coreQuestionAtIndex):
            return True
        elif isinstance(self._coreQuestionAtIndex, Page) and \
                not self._coreQuestionAtIndex.allowClosing:
            return True
        else:
            return super(HeadOpenSection, self).canMoveForward

    @property
    def jumplist(self):
        '''
        .. todo:: Jumplist wird nicht richtig generiert

        '''
        # return value: [([0,1], 'JumpText'), ([1], 'JumpText'), ...]

        jumplist = []
        for item in super(HeadOpenSection, self).jumplist:
            if len(item[0]) == 0 or item[0][0] <= self.maxQuestionIndex:
                jumplist.append(item)

        return jumplist

    def moveForward(self):
        '''
        '''
        if self._maxQuestionIndex == self._currentQuestionIndex:
            if isinstance(self._coreQuestionAtIndex, Page):
                self._coreQuestionAtIndex.closeQuestion()

            elif not self._coreQuestionAtIndex.canMoveForward:  # self._coreQuestionAtIndex is instance of PageGroup and at the last item
                if not HeadOpenSection._allowClosingAllChildQuestions(self._coreQuestionAtIndex):
                    # TODO handle if not all questions are closable.
                    self._coreQuestionAtIndex.appendItem(HeadOpenSectionCantClose())

                else:  # all child question at current index allow closing
                    HeadOpenSection._closeChildQuestions(self._coreQuestionAtIndex)

        super(HeadOpenSection, self).moveForward()
        self._maxQuestionIndex = self._currentQuestionIndex

    def moveToLast(self):
        self._currentQuestionIndex = self._maxQuestionIndex

        if self._questionList[self._currentQuestionIndex].shouldBeShown:
            if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
                self._questionList[self._currentQuestionIndex].moveToLast()
            return
        else:
            self.moveBackward()

    def leave(self, direction):
        if direction == Direction.FORWARD:
            logger.debug("Leaving HeadOpenSection direction forward. closing last question.", self._experiment)
            if isinstance(self._coreQuestionAtIndex, Page):
                self._coreQuestionAtIndex.closeQuestion()
            else:
                HeadOpenSection._closeChildQuestions(self._coreQuestionAtIndex)
        super(HeadOpenSection, self).leave(direction)

    @staticmethod
    def _allowClosingAllChildQuestions(questionGroup, L=None):
        allowClosing = True
        for item in questionGroup._questionList:
            if isinstance(item, PageGroup):
                allowClosing = allowClosing and HeadOpenSection._allowClosingAllChildQuestions(item, L)
            elif not item.allowClosing:  # item is instance of Page and does not allow closing
                allowClosing = False
                if L is not None:
                    L.append(item)

        return allowClosing

    @staticmethod
    def _closeChildQuestions(questionGroup):
        for item in questionGroup._questionList:
            if isinstance(item, Page):
                item.closeQuestion()
            else:
                HeadOpenSection._closeChildQuestions(item)

    @staticmethod
    def _setShowCorrectiveHints(coreQuestion, b):
        if isinstance(coreQuestion, Page):
            coreQuestion.showCorrectiveHints = b
        else:
            questionGroup = coreQuestion
            for item in questionGroup._questionList:
                HeadOpenSection._setShowCorrectiveHints(item, b)


class SegmentedSection(HeadOpenSection):
    @property
    def canMoveBackward(self):
        if isinstance(self._coreQuestionAtIndex, PageGroup):
            return self._coreQuestionAtIndex.canMoveBackward
        return False

    def moveToFirst(self):
        pass

    def moveToLast(self):
        pass

    def moveToPosition(self, posList):
        if self._currentQuestionIndex != posList[0]:
            raise MoveError()

        super(SegmentedSection, self).moveToPosition(posList)

    @property
    def jumplist(self):
        '''
        .. todo:: Besser implementieren und überlegen, wann jumplist angezeigt werden soll und wann nicht. Lösung auf höherer Ebene?
        .. todo:: Es zeigt sich, dass die implementierung nicht richtig durchdacht war

        '''
        jumplist = []
        for item in super(HeadOpenSection, self).jumplist:
            if len(item[0]) == 0 or item[0][0] == self._currentQuestionIndex:
                jumplist.append(item)

        # if len(jumplist) <= 1:
            # jumplist = []

        return jumplist
