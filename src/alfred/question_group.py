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
    def question_list(self):
        return self._questionList

    @property
    def data(self):
        data = super(PageGroup, self).data
        data['subtreeData'] = []
        for qCore in self._questionList:
            data['subtreeData'].append(qCore.data)

        return data

    @property
    def current_question(self):
        return self._questionList[self._currentQuestionIndex].current_question if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) else self._questionList[self._currentQuestionIndex]

    @property
    def current_title(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].current_title is not None:
            return self._questionList[self._currentQuestionIndex].current_title

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].title is not None:
            return self._questionList[self._currentQuestionIndex].title

        return self.title

    @property
    def current_subtitle(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].current_subtitle is not None:
            return self._questionList[self._currentQuestionIndex].current_subtitle

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].subtitle is not None:
            return self._questionList[self._currentQuestionIndex].subtitle

        return self.subtitle

    @property
    def current_status_text(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].current_status_text is not None:
            return self._questionList[self._currentQuestionIndex].current_status_text

        if isinstance(self._questionList[self._currentQuestionIndex], Page) and self._questionList[self._currentQuestionIndex].statustext is not None:
            return self._questionList[self._currentQuestionIndex].statustext

        return self.statustext

    @PageCore.should_be_shown.getter
    def should_be_shown(self):
        '''return true wenn should_be_shown nicht auf False gesetzt wurde und mindestens eine Frage angezeigt werden will'''
        return super(PageGroup, self).should_be_shown and reduce(lambda b, qCore: b or qCore.should_be_shown, self._questionList, False)

    def allow_leaving(self, direction):
        return self._questionList[self._currentQuestionIndex].allow_leaving(direction)

    def enter(self):
        logger.debug(u"Entering PageGroup %s" % self.tag, self._experiment)
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.enter()

    def leave(self, direction):
        assert(self.allow_leaving(direction))
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(direction)

        logger.debug(u"Leaving PageGroup %s in direction %s" % (self.tag, Direction.to_str(direction)), self._experiment)

    @property
    def jumplist(self):
        # return value: [([0,1], 'JumpText', coreQuestion), ([1], 'JumpText', coreQuestion), ...]

        jumplist = []
        if self.is_jumpable:
            jumplist = [([], self.jumptext, self)]

        for i in range(0, len(self._questionList)):
            if isinstance(self._questionList[i], PageGroup):
                for jumpItem in self._questionList[i].jumplist:
                    assert len(jumpItem) == 3
                    jumpItem[0].reverse()
                    jumpItem[0].append(i)
                    jumpItem[0].reverse()
                    jumplist.append(jumpItem)
            elif isinstance(self._questionList[i], Page) and self._questionList[i].is_jumpable:
                jumplist.append(([i], self._questionList[i].jumptext, self._questionList[i]))

        return jumplist

    def randomize(self, deep=False):
        self.generate_unset_tags_in_subtree()
        shuffle(self._questionList)

        if deep:
            for item in self._questionList:
                if isinstance(item, PageGroup):
                    item.randomize(True)

    def added_to_experiment(self, exp):
        self._experiment = exp

        for question in self._questionList:
            question.added_to_experiment(self._experiment)

    def append_item(self, item):
        if not isinstance(item, PageCore):
            raise TypeError("question must be an instance of PageCore")

        self._questionList.append(item)
        item.added_to_section(self)

        if self._experiment is not None:
            item.added_to_experiment(self._experiment)

        self.generate_unset_tags_in_subtree()

    def append_items(self, *items):
        for item in items:
            self.append_item(item)

    def generate_unset_tags_in_subtree(self):
        for i in range(0, len(self._questionList)):
            if self._questionList[i].tag is None:
                self._questionList[i].tag = str(i + 1)

            if isinstance(self._questionList[i], PageGroup):
                self._questionList[i].generate_unset_tags_in_subtree()

    @property
    def can_move_backward(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].can_move_backward:
            return True

        return reduce(lambda b, qCore: b or qCore.should_be_shown, self._questionList[:self._currentQuestionIndex], False)

    @property
    def can_move_forward(self):
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) and self._questionList[self._currentQuestionIndex].can_move_forward:
            return True

        return reduce(lambda b, qCore: b or qCore.should_be_shown, self._questionList[self._currentQuestionIndex + 1:], False)

    def move_forward(self):
        # test if moving is possible and leaving is allowed
        if not (self.can_move_forward and self.allow_leaving(Direction.FORWARD)):
            raise MoveError()

        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) \
                and self._questionList[self._currentQuestionIndex].can_move_forward:
            self._questionList[self._currentQuestionIndex].move_forward()

        else:
            # if current_question is QG: call leave
            if isinstance(self._core_question_at_index, PageGroup):
                self._core_question_at_index.leave(Direction.FORWARD)
            for index in range(self._currentQuestionIndex + 1, len(self._questionList)):
                if self._questionList[index].should_be_shown:
                    self._currentQuestionIndex = index
                    if isinstance(self._questionList[index], PageGroup):
                        self._questionList[index].move_to_first()
                        self._core_question_at_index.enter()
                    break

    def move_backward(self):
        if not (self.can_move_backward and self.allow_leaving(Direction.BACKWARD)):
            raise MoveError()

        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup) \
                and self._questionList[self._currentQuestionIndex].can_move_backward:
            self._questionList[self._currentQuestionIndex].move_backward()

        else:
            # if current_question is QG: call leave
            if isinstance(self._core_question_at_index, PageGroup):
                self._core_question_at_index.leave(Direction.BACKWARD)
            for index in range(self._currentQuestionIndex - 1, -1, -1):
                if self._questionList[index].should_be_shown:
                    self._currentQuestionIndex = index
                    if isinstance(self._questionList[index], PageGroup):
                        self._questionList[index].move_to_last()
                        self._core_question_at_index.enter()
                    break

    def move_to_first(self):
        logger.debug(u"QG %s: move to first" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)
        self._currentQuestionIndex = 0
        if self._questionList[0].should_be_shown:
            if isinstance(self._questionList[0], PageGroup):
                self._core_question_at_index.enter()
                self._questionList[0].move_to_first()
        else:
            self.move_forward()

    def move_to_last(self):
        logger.debug(u"QG %s: move to last" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)
        self._currentQuestionIndex = len(self._questionList) - 1
        if self._questionList[self._currentQuestionIndex].should_be_shown:
            if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
                self._core_question_at_index.enter()
                self._questionList[0].move_to_last()
        else:
            self.move_backward()

    def move_to_position(self, posList):
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()

        if not isinstance(posList, list) or len(posList) == 0 or not reduce(lambda b, item: b and isinstance(item, int), posList, True):
            raise TypeError("posList must be an list of int with at least one item")

        if not 0 <= posList[0] < len(self._questionList):
            raise MoveError("posList enthaelt eine falsche postionsanganbe.")

        if not self._questionList[posList[0]].should_be_shown:
            raise MoveError("Die Angegebene Position kann nicht angezeigt werden")

        if isinstance(self._questionList[posList[0]], Page) and 1 < len(posList):
            raise MoveError("posList spezifiziert genauer als moeglich.")

        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)

        self._currentQuestionIndex = posList[0]
        if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
            self._core_question_at_index.enter()
            if len(posList) == 1:
                self._questionList[self._currentQuestionIndex].move_to_first()
            else:
                self._questionList[self._currentQuestionIndex].move_to_position(posList[1:])

    @property
    def _core_question_at_index(self):
        return self._questionList[self._currentQuestionIndex]


class HeadOpenSection(PageGroup):
    def __init__(self, **kwargs):
        super(HeadOpenSection, self).__init__(**kwargs)
        self._maxQuestionIndex = 0

    @property
    def max_question_index(self):
        return self._maxQuestionIndex

    def allow_leaving(self, direction):
        if direction != Direction.FORWARD:
            return super(HeadOpenSection, self).allow_leaving(direction)

        # direction is Direction.FORWARD

        if isinstance(self._core_question_at_index, Page):
            HeadOpenSection._set_show_corrective_hints(self._core_question_at_index, True)
            return self._core_question_at_index.allow_closing and super(HeadOpenSection, self).allow_leaving(direction)
        else:  # currentCoreQuestion is Group
            if not self._core_question_at_index.can_move_forward:
                HeadOpenSection._set_show_corrective_hints(self._core_question_at_index, True)
                return HeadOpenSection._allow_closing_all_child_questions(self._core_question_at_index) and super(HeadOpenSection, self).allow_leaving(direction)
            else:
                return super(HeadOpenSection, self).allow_leaving(direction)

    @property
    def can_move_forward(self):
        # wenn die aktuelle Fragengruppe oder Frage nicht geschlossen werden
        # kann, return true. Dann kann die HeadOpenSection darauf reagieren und die
        # Frage nochmal mit den corrective Hints anzeigen.
        if isinstance(self._core_question_at_index, PageGroup) and \
                not self._core_question_at_index.can_move_forward and \
                not HeadOpenSection._allow_closing_all_child_questions(self._core_question_at_index):
            return True
        elif isinstance(self._core_question_at_index, Page) and \
                not self._core_question_at_index.allow_closing:
            return True
        else:
            return super(HeadOpenSection, self).can_move_forward

    @property
    def jumplist(self):
        '''
        .. todo:: Jumplist wird nicht richtig generiert

        '''
        # return value: [([0,1], 'JumpText'), ([1], 'JumpText'), ...]

        jumplist = []
        for item in super(HeadOpenSection, self).jumplist:
            if len(item[0]) == 0 or item[0][0] <= self.max_question_index:
                jumplist.append(item)

        return jumplist

    def move_forward(self):
        '''
        '''
        if self._maxQuestionIndex == self._currentQuestionIndex:
            if isinstance(self._core_question_at_index, Page):
                self._core_question_at_index.closeQuestion()

            elif not self._core_question_at_index.can_move_forward:  # self._core_question_at_index is instance of PageGroup and at the last item
                if not HeadOpenSection._allow_closing_all_child_questions(self._core_question_at_index):
                    # TODO handle if not all questions are closable.
                    self._core_question_at_index.append_item(HeadOpenSectionCantClose())

                else:  # all child question at current index allow closing
                    HeadOpenSection._close_child_questions(self._core_question_at_index)

        super(HeadOpenSection, self).move_forward()
        self._maxQuestionIndex = self._currentQuestionIndex

    def move_to_last(self):
        self._currentQuestionIndex = self._maxQuestionIndex

        if self._questionList[self._currentQuestionIndex].should_be_shown:
            if isinstance(self._questionList[self._currentQuestionIndex], PageGroup):
                self._questionList[self._currentQuestionIndex].move_to_last()
            return
        else:
            self.move_backward()

    def leave(self, direction):
        if direction == Direction.FORWARD:
            logger.debug("Leaving HeadOpenSection direction forward. closing last question.", self._experiment)
            if isinstance(self._core_question_at_index, Page):
                self._core_question_at_index.closeQuestion()
            else:
                HeadOpenSection._close_child_questions(self._core_question_at_index)
        super(HeadOpenSection, self).leave(direction)

    @staticmethod
    def _allow_closing_all_child_questions(questionGroup, L=None):
        allow_closing = True
        for item in questionGroup._questionList:
            if isinstance(item, PageGroup):
                allow_closing = allow_closing and HeadOpenSection._allow_closing_all_child_questions(item, L)
            elif not item.allow_closing:  # item is instance of Page and does not allow closing
                allow_closing = False
                if L is not None:
                    L.append(item)

        return allow_closing

    @staticmethod
    def _close_child_questions(questionGroup):
        for item in questionGroup._questionList:
            if isinstance(item, Page):
                item.closeQuestion()
            else:
                HeadOpenSection._close_child_questions(item)

    @staticmethod
    def _set_show_corrective_hints(coreQuestion, b):
        if isinstance(coreQuestion, Page):
            coreQuestion.show_corrective_hints = b
        else:
            questionGroup = coreQuestion
            for item in questionGroup._questionList:
                HeadOpenSection._set_show_corrective_hints(item, b)


class SegmentedSection(HeadOpenSection):
    @property
    def can_move_backward(self):
        if isinstance(self._core_question_at_index, PageGroup):
            return self._core_question_at_index.can_move_backward
        return False

    def move_to_first(self):
        pass

    def move_to_last(self):
        pass

    def move_to_position(self, posList):
        if self._currentQuestionIndex != posList[0]:
            raise MoveError()

        super(SegmentedSection, self).move_to_position(posList)

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
