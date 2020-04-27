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

from ._core import ContentCore, Direction
from .page import PageCore, HeadOpenSectionCantClose
from .exceptions import MoveError
from random import shuffle


class Section(ContentCore):

    def __init__(self, **kwargs):
        super(Section, self).__init__(**kwargs)

        self._page_list = []
        self._currentPageIndex = 0
        self._should_be_shown = True
        self._log = [] # insert tuple with ('type', msg) for logger

    def __str__(self):
        s = "Section (tag = " + self.tag + ", pages:[" + str(self._page_list) + "]"
        return s

    @property
    def page_list(self):
        return self._page_list

    @property
    def data(self):
        data = super(Section, self).data
        data['subtree_data'] = []
        for q_core in self._page_list:
            data['subtree_data'].append(q_core.data)

        return data

    @property
    def current_page(self):
        return self._page_list[self._currentPageIndex].current_page if isinstance(self._page_list[self._currentPageIndex], Section) else self._page_list[self._currentPageIndex]

    @property
    def current_title(self):
        if isinstance(self._page_list[self._currentPageIndex], Section) and self._page_list[self._currentPageIndex].current_title is not None:
            return self._page_list[self._currentPageIndex].current_title

        if isinstance(self._page_list[self._currentPageIndex], PageCore) and self._page_list[self._currentPageIndex].title is not None:
            return self._page_list[self._currentPageIndex].title

        return self.title

    @property
    def current_subtitle(self):
        if isinstance(self._page_list[self._currentPageIndex], Section) and self._page_list[self._currentPageIndex].current_subtitle is not None:
            return self._page_list[self._currentPageIndex].current_subtitle

        if isinstance(self._page_list[self._currentPageIndex], PageCore) and self._page_list[self._currentPageIndex].subtitle is not None:
            return self._page_list[self._currentPageIndex].subtitle

        return self.subtitle

    @property
    def current_status_text(self):
        if isinstance(self._page_list[self._currentPageIndex], Section) and self._page_list[self._currentPageIndex].current_status_text is not None:
            return self._page_list[self._currentPageIndex].current_status_text

        if isinstance(self._page_list[self._currentPageIndex], PageCore) and self._page_list[self._currentPageIndex].statustext is not None:
            return self._page_list[self._currentPageIndex].statustext

        return self.statustext

    @ContentCore.should_be_shown.getter # pylint: disable=no-member
    def should_be_shown(self):
        '''return true wenn should_be_shown nicht auf False gesetzt wurde und mindestens eine Frage angezeigt werden will'''
        return super(Section, self).should_be_shown and reduce(lambda b, q_core: b or q_core.should_be_shown, self._page_list, False)

    def allow_leaving(self, direction):
        return self._page_list[self._currentPageIndex].allow_leaving(direction)

    def enter(self):
        logger.debug(u"Entering Section %s" % self.tag, self._experiment)
        if isinstance(self._core_page_at_index, Section):
            self._core_page_at_index.enter()

    def leave(self, direction):
        assert(self.allow_leaving(direction))
        if isinstance(self._core_page_at_index, Section):
            self._core_page_at_index.leave(direction)

        logger.debug(u"Leaving Section %s in direction %s" % (self.tag, Direction.to_str(direction)), self._experiment)

    @property
    def jumplist(self):
        # return value: [([0,1], 'JumpText', corePage), ([1], 'JumpText', corePage), ...]

        jumplist = []
        if self.is_jumpable:
            jumplist = [([], self.jumptext, self)]

        for i in range(0, len(self._page_list)):
            if isinstance(self._page_list[i], Section):
                for jump_item in self._page_list[i].jumplist:
                    assert len(jump_item) == 3
                    jump_item[0].reverse()
                    jump_item[0].append(i)
                    jump_item[0].reverse()
                    jumplist.append(jump_item)
            elif isinstance(self._page_list[i], PageCore) and self._page_list[i].is_jumpable:
                jumplist.append(([i], self._page_list[i].jumptext, self._page_list[i]))

        return jumplist

    def randomize(self, deep=False):
        self.generate_unset_tags_in_subtree()
        shuffle(self._page_list)

        if deep:
            for item in self._page_list:
                if isinstance(item, Section):
                    item.randomize(True)

    def print_log(self):
        for category, msg in self._log:
            if category == 'debug':
                logger.debug(msg, self._experiment)
            if category == 'info':
                logger.info(msg, self._experiment)
            if category == 'warning':
                logger.warning(msg, self._experiment)
            if category == 'error':
                logger.error(msg, self._experiment)
            if category == 'critical':
                logger.critical(msg, self._experiment)
            if category == 'log':
                logger.log(msg, self._experiment)
            if category == 'exception':
                logger.exception(msg, self._experiment)

    def added_to_experiment(self, exp):
        self._experiment = exp
        self.print_log()

        for page in self._page_list:
            page.added_to_experiment(self._experiment)
            page.print_log()

    def append_item(self, item):
        self._log.append(('warning', "section.append_item() is deprecated. Use section.append() instead."))
        self.append(item)

    def append_items(self, *items):
        self._log.append(('warning', "section.append_items() is deprecated. Use section.append() instead."))

        for item in items:
            self.append(item)

    def append(self, *items):
        for item in items:
            self._page_list.append(item)
            item.added_to_section(self)

            if self._experiment is not None:
                item.added_to_experiment(self._experiment)

            self.generate_unset_tags_in_subtree()

    def generate_unset_tags_in_subtree(self):
        for i in range(0, len(self._page_list)):
            if self._page_list[i].tag is None:
                self._page_list[i].tag = str(i + 1)

            if isinstance(self._page_list[i], Section):
                self._page_list[i].generate_unset_tags_in_subtree()

    @property
    def can_move_backward(self):
        if isinstance(self._page_list[self._currentPageIndex], Section) and self._page_list[self._currentPageIndex].can_move_backward:
            return True

        return reduce(lambda b, q_core: b or q_core.should_be_shown, self._page_list[:self._currentPageIndex], False)

    @property
    def can_move_forward(self):
        if isinstance(self._page_list[self._currentPageIndex], Section) and self._page_list[self._currentPageIndex].can_move_forward:
            return True

        return reduce(lambda b, q_core: b or q_core.should_be_shown, self._page_list[self._currentPageIndex + 1:], False)

    def move_forward(self):
        # test if moving is possible and leaving is allowed
        if not (self.can_move_forward and self.allow_leaving(Direction.FORWARD)):
            raise MoveError()

        if isinstance(self._page_list[self._currentPageIndex], Section) \
                and self._page_list[self._currentPageIndex].can_move_forward:
            self._page_list[self._currentPageIndex].move_forward()

        else:
            # if current_page is QG: call leave
            if isinstance(self._core_page_at_index, Section):
                self._core_page_at_index.leave(Direction.FORWARD)
            for index in range(self._currentPageIndex + 1, len(self._page_list)):
                if self._page_list[index].should_be_shown:
                    self._currentPageIndex = index
                    if isinstance(self._page_list[index], Section):
                        self._page_list[index].move_to_first()
                        self._core_page_at_index.enter()
                    break

    def move_backward(self):
        if not (self.can_move_backward and self.allow_leaving(Direction.BACKWARD)):
            raise MoveError()

        if isinstance(self._page_list[self._currentPageIndex], Section) \
                and self._page_list[self._currentPageIndex].can_move_backward:
            self._page_list[self._currentPageIndex].move_backward()

        else:
            # if current_page is QG: call leave
            if isinstance(self._core_page_at_index, Section):
                self._core_page_at_index.leave(Direction.BACKWARD)
            for index in range(self._currentPageIndex - 1, -1, -1):
                if self._page_list[index].should_be_shown:
                    self._currentPageIndex = index
                    if isinstance(self._page_list[index], Section):
                        self._page_list[index].move_to_last()
                        self._core_page_at_index.enter()
                    break

    def move_to_first(self):
        logger.debug(u"QG %s: move to first" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_page_at_index, Section):
            self._core_page_at_index.leave(Direction.JUMP)
        self._currentPageIndex = 0
        if self._page_list[0].should_be_shown:
            if isinstance(self._page_list[0], Section):
                self._core_page_at_index.enter()
                self._page_list[0].move_to_first()
        else:
            self.move_forward()

    def move_to_last(self):
        logger.debug(u"QG %s: move to last" % self.tag, self._experiment)
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()
        if isinstance(self._core_page_at_index, Section):
            self._core_page_at_index.leave(Direction.JUMP)
        self._currentPageIndex = len(self._page_list) - 1
        if self._page_list[self._currentPageIndex].should_be_shown:
            if isinstance(self._page_list[self._currentPageIndex], Section):
                self._core_page_at_index.enter()
                self._page_list[0].move_to_last()
        else:
            self.move_backward()

    def move_to_position(self, pos_list):
        if not self.allow_leaving(Direction.JUMP):
            raise MoveError()

        if not isinstance(pos_list, list) or len(pos_list) == 0 or not reduce(lambda b, item: b and isinstance(item, int), pos_list, True):
            raise TypeError("pos_list must be an list of int with at least one item")

        if not 0 <= pos_list[0] < len(self._page_list):
            raise MoveError("pos_list enthaelt eine falsche postionsanganbe.")

        if not self._page_list[pos_list[0]].should_be_shown:
            raise MoveError("Die Angegebene Position kann nicht angezeigt werden")

        if isinstance(self._page_list[pos_list[0]], PageCore) and 1 < len(pos_list):
            raise MoveError("pos_list spezifiziert genauer als moeglich.")

        if isinstance(self._core_page_at_index, Section):
            self._core_page_at_index.leave(Direction.JUMP)

        self._currentPageIndex = pos_list[0]
        if isinstance(self._page_list[self._currentPageIndex], Section):
            self._core_page_at_index.enter()
            if len(pos_list) == 1:
                self._page_list[self._currentPageIndex].move_to_first()
            else:
                self._page_list[self._currentPageIndex].move_to_position(pos_list[1:])

    @property
    def _core_page_at_index(self):
        return self._page_list[self._currentPageIndex]


class HeadOpenSection(Section):
    def __init__(self, **kwargs):
        super(HeadOpenSection, self).__init__(**kwargs)
        self._maxPageIndex = 0

    @property
    def max_page_index(self):
        return self._maxPageIndex

    def allow_leaving(self, direction):
        if direction != Direction.FORWARD:
            return super(HeadOpenSection, self).allow_leaving(direction)

        # direction is Direction.FORWARD

        if isinstance(self._core_page_at_index, PageCore):
            HeadOpenSection._set_show_corrective_hints(self._core_page_at_index, True)
            return self._core_page_at_index.allow_closing and super(HeadOpenSection, self).allow_leaving(direction)
        else:  # currentCorePage is Group
            if not self._core_page_at_index.can_move_forward:
                HeadOpenSection._set_show_corrective_hints(self._core_page_at_index, True)
                return HeadOpenSection._allow_closing_all_child_pages(self._core_page_at_index) and super(HeadOpenSection, self).allow_leaving(direction)
            else:
                return super(HeadOpenSection, self).allow_leaving(direction)

    @property
    def can_move_forward(self):
        # wenn die aktuelle Fragengruppe oder Frage nicht geschlossen werden
        # kann, return true. Dann kann die HeadOpenSection darauf reagieren und die
        # Frage nochmal mit den corrective Hints anzeigen.
        if isinstance(self._core_page_at_index, Section) and \
                not self._core_page_at_index.can_move_forward and \
                not HeadOpenSection._allow_closing_all_child_pages(self._core_page_at_index):
            return True
        elif isinstance(self._core_page_at_index, PageCore) and \
                not self._core_page_at_index.allow_closing:
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
            if len(item[0]) == 0 or item[0][0] <= self.max_page_index:
                jumplist.append(item)

        return jumplist

    def move_forward(self):
        '''
        '''
        if self._maxPageIndex == self._currentPageIndex:
            if isinstance(self._core_page_at_index, PageCore):
                self._core_page_at_index.close_page()

            elif not self._core_page_at_index.can_move_forward:  # self._core_page_at_index is instance of Section and at the last item
                if not HeadOpenSection._allow_closing_all_child_pages(self._core_page_at_index):
                    # TODO handle if not all pages are closable.
                    self._core_page_at_index.append(HeadOpenSectionCantClose())

                else:  # all child page at current index allow closing
                    HeadOpenSection._close_child_pages(self._core_page_at_index)

        super(HeadOpenSection, self).move_forward()
        self._maxPageIndex = self._currentPageIndex

    def move_to_last(self):
        self._currentPageIndex = self._maxPageIndex

        if self._page_list[self._currentPageIndex].should_be_shown:
            if isinstance(self._page_list[self._currentPageIndex], Section):
                self._page_list[self._currentPageIndex].move_to_last()
            return
        else:
            self.move_backward()

    def leave(self, direction):
        if direction == Direction.FORWARD:
            logger.debug("Leaving HeadOpenSection direction forward. closing last page.", self._experiment)
            if isinstance(self._core_page_at_index, PageCore):
                self._core_page_at_index.close_page()
            else:
                HeadOpenSection._close_child_pages(self._core_page_at_index)
        super(HeadOpenSection, self).leave(direction)

    @staticmethod
    def _allow_closing_all_child_pages(section, L=None):
        allow_closing = True
        for item in section._page_list:
            if isinstance(item, Section):
                allow_closing = allow_closing and HeadOpenSection._allow_closing_all_child_pages(item, L)
            elif not item.allow_closing:  # item is instance of Page and does not allow closing
                allow_closing = False
                if L is not None:
                    L.append(item)

        return allow_closing

    @staticmethod
    def _close_child_pages(section):
        for item in section._page_list:
            if isinstance(item, PageCore):
                item.close_page()
            else:
                HeadOpenSection._close_child_pages(item)

    @staticmethod
    def _set_show_corrective_hints(corePage, b):
        if isinstance(corePage, PageCore):
            corePage.show_corrective_hints = b
        else:
            section = corePage
            for item in section._page_list:
                HeadOpenSection._set_show_corrective_hints(item, b)


class SegmentedSection(HeadOpenSection):
    @property
    def can_move_backward(self):
        if isinstance(self._core_page_at_index, Section):
            return self._core_page_at_index.can_move_backward
        return False

    def move_to_first(self):
        pass

    def move_to_last(self):
        pass

    def move_to_position(self, pos_list):
        if self._currentPageIndex != pos_list[0]:
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
            if len(item[0]) == 0 or item[0][0] == self._currentPageIndex:
                jumplist.append(item)

        # if len(jumplist) <= 1:
            # jumplist = []

        return jumplist
