# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
'''
from __future__ import absolute_import

from builtins import str
from builtins import range
from . import alfredlog
from functools import reduce
logger = alfredlog.get_logger(__name__)

from ._core import PageCore, Direction
from .question import Page, HeadOpenSectionCantClose
from .exceptions import MoveError
from random import shuffle


class PageGroup(PageCore):

    def __init__(self, **kwargs):
        super(PageGroup, self).__init__(**kwargs)

        self._question_list = []
        self._current_question_index = 0
        self._should_be_shown = True

    def __str__(self):
        s = "PageGroup (tag = " + self.tag + ", questions:[" + str(self._question_list) + "]"
        return s

    @property
    def question_list(self):
        return self._question_list

    @property
    def data(self):
        data = super(PageGroup, self).data
        data['subtree_data'] = []
        for q_core in self._question_list:
            data['subtree_data'].append(q_core.data)

        return data

    @property
    def current_question(self):
        return self._question_list[self._current_question_index].current_question if isinstance(self._question_list[self._current_question_index], PageGroup) else self._question_list[self._current_question_index]

    @property
    def current_title(self):
        if isinstance(self._question_list[self._current_question_index], PageGroup) and self._question_list[self._current_question_index].current_title is not None:
            return self._question_list[self._current_question_index].current_title

        if isinstance(self._question_list[self._current_question_index], Page) and self._question_list[self._current_question_index].title is not None:
            return self._question_list[self._current_question_index].title

        return self.title

    @property
    def current_subtitle(self):
        if isinstance(self._question_list[self._current_question_index], PageGroup) and self._question_list[self._current_question_index].current_subtitle is not None:
            return self._question_list[self._current_question_index].current_subtitle

        if isinstance(self._question_list[self._current_question_index], Page) and self._question_list[self._current_question_index].subtitle is not None:
            return self._question_list[self._current_question_index].subtitle

        return self.subtitle

    @property
    def current_status_text(self):
        if isinstance(self._question_list[self._current_question_index], PageGroup) and self._question_list[self._current_question_index].current_status_text is not None:
            return self._question_list[self._current_question_index].current_status_text

        if isinstance(self._question_list[self._current_question_index], Page) and self._question_list[self._current_question_index].statustext is not None:
            return self._question_list[self._current_question_index].statustext

        return self.statustext

    @PageCore.should_be_shown.getter
    def should_be_shown(self):
        '''return true wenn should_be_shown nicht auf False gesetzt wurde und mindestens eine Frage angezeigt werden will'''
        return super(PageGroup, self).should_be_shown and reduce(lambda b, q_core: b or q_core.should_be_shown, self._question_list, False)

    def allow_leaving(self, direction):
        return self._question_list[self._current_question_index].allow_leaving(direction)

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
        # return value: [([0,1], 'JumpText', core_page), ([1], 'JumpText', core_page), ...]

        jumplist = []
        if self.is_jumpable:
            jumplist = [([], self.jumptext, self)]

        for i in range(0, len(self._question_list)):
            if isinstance(self._question_list[i], PageGroup):
                for jump_item in self._question_list[i].jumplist:
                    assert len(jump_item) == 3
                    jump_item[0].reverse()
                    jump_item[0].append(i)
                    jump_item[0].reverse()
                    jumplist.append(jump_item)
            elif isinstance(self._question_list[i], Page) and self._question_list[i].is_jumpable:
                jumplist.append(([i], self._question_list[i].jumptext, self._question_list[i]))

        return jumplist

    def randomize(self, deep=False):
        self.generate_unset_tags_in_subtree()
        shuffle(self._question_list)

        if deep:
            for item in self._question_list:
                if isinstance(item, PageGroup):
                    item.randomize(True)

    def added_to_experiment(self, exp):
        self._experiment = exp

        for question in self._question_list:
            question.added_to_experiment(self._experiment)

    def append_item(self, item):
        if not isinstance(item, PageCore):
            raise TypeError("question must be an instance of PageCore")

        self._question_list.append(item)
        item.added_to_section(self)

        if self._experiment is not None:
            item.added_to_experiment(self._experiment)

        self.generate_unset_tags_in_subtree()

    def append_items(self, *items):
        for item in items:
            self.append_item(item)

    def generate_unset_tags_in_subtree(self):
        for i in range(0, len(self._question_list)):
            if self._question_list[i].tag is None:
                self._question_list[i].tag = str(i + 1)

            if isinstance(self._question_list[i], PageGroup):
                self._question_list[i].generate_unset_tags_in_subtree()

    @property
    def can_move_backward(self):
        if isinstance(self._question_list[self._current_question_index], PageGroup) and self._question_list[self._current_question_index].can_move_backward:
            return True

        return reduce(lambda b, q_core: b or q_core.should_be_shown, self._question_list[:self._current_question_index], False)

    @property
    def can_move_forward(self):
        if isinstance(self._question_list[self._current_question_index], PageGroup) and self._question_list[self._current_question_index].can_move_forward:
            return True

        return reduce(lambda b, q_core: b or q_core.should_be_shown, self._question_list[self._current_question_index + 1:], False)

    def move_forward(self):
        # test if moving is possible and leaving is allowed
        if not (self.can_move_forward and self.allow_leaving(Direction.FORWARD)):
            raise MoveError()

        if isinstance(self._question_list[self._current_question_index], PageGroup) \
                and self._question_list[self._current_question_index].can_move_forward:
            self._question_list[self._current_question_index].move_forward()

        else:
            # if current_question is QG: call leave
            if isinstance(self._core_question_at_index, PageGroup):
                self._core_question_at_index.leave(Direction.FORWARD)
            for index in range(self._current_question_index + 1, len(self._question_list)):
                if self._question_list[index].should_be_shown:
                    self._current_question_index = index
                    if isinstance(self._question_list[index], PageGroup):
                        self._question_list[index].move_to_first()
                        self._core_question_at_index.enter()
                    break

    def move_backward(self):
        if not (self.can_move_backward and self.allow_leaving(Direction.BACKWARD)):
            raise MoveError()

        if isinstance(self._question_list[self._current_question_index], PageGroup) \
                and self._question_list[self._current_question_index].can_move_backward:
            self._question_list[self._current_question_index].move_backward()

        else:
            # if current_question is QG: call leave
            if isinstance(self._core_question_at_index, PageGroup):
                self._core_question_at_index.leave(Direction.BACKWARD)
            for index in range(self._current_question_index - 1, -1, -1):
                if self._question_list[index].should_be_shown:
                    self._current_question_index = index
                    if isinstance(self._question_list[index], PageGroup):
                        self._question_list[index].move_to_last()
                        self._core_question_at_index.enter()
                    break

    def move_to_first(self):
        logger.debug(u"QG %s: move to first" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)
        self._current_question_index = 0
        if self._question_list[0].should_be_shown:
            if isinstance(self._question_list[0], PageGroup):
                self._core_question_at_index.enter()
                self._question_list[0].move_to_first()
        else:
            self.move_forward()

    def move_to_last(self):
        logger.debug(u"QG %s: move to last" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)
        self._current_question_index = len(self._question_list) - 1
        if self._question_list[self._current_question_index].should_be_shown:
            if isinstance(self._question_list[self._current_question_index], PageGroup):
                self._core_question_at_index.enter()
                self._question_list[0].move_to_last()
        else:
            self.move_backward()

    def move_to_position(self, pos_list):
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()

        if not isinstance(pos_list, list) or len(pos_list) == 0 or not reduce(lambda b, item: b and isinstance(item, int), pos_list, True):
            raise TypeError("pos_list must be an list of int with at least one item")

        if not 0 <= pos_list[0] < len(self._question_list):
            raise MoveError("pos_list enthaelt eine falsche postionsanganbe.")

        if not self._question_list[pos_list[0]].should_be_shown:
            raise MoveError("Die Angegebene Position kann nicht angezeigt werden")

        if isinstance(self._question_list[pos_list[0]], Page) and 1 < len(pos_list):
            raise MoveError("pos_list spezifiziert genauer als moeglich.")

        if isinstance(self._core_question_at_index, PageGroup):
            self._core_question_at_index.leave(Direction.JUMP)

        self._current_question_index = pos_list[0]
        if isinstance(self._question_list[self._current_question_index], PageGroup):
            self._core_question_at_index.enter()
            if len(pos_list) == 1:
                self._question_list[self._current_question_index].move_to_first()
            else:
                self._question_list[self._current_question_index].move_to_position(pos_list[1:])

    @property
    def _core_question_at_index(self):
        return self._question_list[self._current_question_index]


class HeadOpenSection(PageGroup):
    def __init__(self, **kwargs):
        super(HeadOpenSection, self).__init__(**kwargs)
        self._max_question_index = 0

    @property
    def max_question_index(self):
        return self._max_question_index

    def allow_leaving(self, direction):
        if direction != Direction.FORWARD:
            return super(HeadOpenSection, self).allow_leaving(direction)

        # direction is Direction.FORWARD

        if isinstance(self._core_question_at_index, Page):
            HeadOpenSection._set_show_corrective_hints(self._core_question_at_index, True)
            return self._core_question_at_index.allow_closing and super(HeadOpenSection, self).allow_leaving(direction)
        else:  # current_core_page is Group
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
        if self._max_question_index == self._current_question_index:
            if isinstance(self._core_question_at_index, Page):
                self._core_question_at_index.close_question()

            elif not self._core_question_at_index.can_move_forward:  # self._core_question_at_index is instance of PageGroup and at the last item
                if not HeadOpenSection._allow_closing_all_child_questions(self._core_question_at_index):
                    # TODO handle if not all questions are closable.
                    self._core_question_at_index.append_item(HeadOpenSectionCantClose())

                else:  # all child question at current index allow closing
                    HeadOpenSection._close_child_questions(self._core_question_at_index)

        super(HeadOpenSection, self).move_forward()
        self._max_question_index = self._current_question_index

    def move_to_last(self):
        self._current_question_index = self._max_question_index

        if self._question_list[self._current_question_index].should_be_shown:
            if isinstance(self._question_list[self._current_question_index], PageGroup):
                self._question_list[self._current_question_index].move_to_last()
            return
        else:
            self.move_backward()

    def leave(self, direction):
        if direction == Direction.FORWARD:
            logger.debug("Leaving HeadOpenSection direction forward. closing last question.", self._experiment)
            if isinstance(self._core_question_at_index, Page):
                self._core_question_at_index.close_question()
            else:
                HeadOpenSection._close_child_questions(self._core_question_at_index)
        super(HeadOpenSection, self).leave(direction)

    @staticmethod
    def _allow_closing_all_child_questions(section, L=None):
        allow_closing = True
        for item in section._question_list:
            if isinstance(item, PageGroup):
                allow_closing = allow_closing and HeadOpenSection._allow_closing_all_child_questions(item, L)
            elif not item.allow_closing:  # item is instance of Page and does not allow closing
                allow_closing = False
                if L is not None:
                    L.append(item)

        return allow_closing

    @staticmethod
    def _close_child_questions(section):
        for item in section._question_list:
            if isinstance(item, Page):
                item.close_question()
            else:
                HeadOpenSection._close_child_questions(item)

    @staticmethod
    def _set_show_corrective_hints(core_page, b):
        if isinstance(core_page, Page):
            core_page.show_corrective_hints = b
        else:
            section = core_page
            for item in section._question_list:
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

    def move_to_position(self, pos_list):
        if self._current_question_index != pos_list[0]:
            raise MoveError()

        super(SegmentedSection, self).move_to_position(pos_list)

    @property
    def jumplist(self):
        '''
        .. todo:: Besser implementieren und überlegen, wann jumplist angezeigt werden soll und wann nicht. Lösung auf höherer Ebene?
        .. todo:: Es zeigt sich, dass die implementierung nicht richtig durchdacht war

        '''
        jumplist = []
        for item in super(HeadOpenSection, self).jumplist:
            if len(item[0]) == 0 or item[0][0] == self._current_question_index:
                jumplist.append(item)

        # if len(jumplist) <= 1:
            # jumplist = []

        return jumplist
