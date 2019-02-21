# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
'''


from builtins import object
import os.path
from uuid import uuid4

import alfred.settings


class QuestionCore(object):
    def __init__(self, tag=None, uid=None, tagAndUid=None, isJumpable=True, jumptext=None,
                 title=None, subtitle=None, statustext=None,
                 shouldBeShownFilterFunction=None, **kwargs):

        if kwargs != {}:
            raise ValueError("parameter '%s' is not supported." % list(kwargs.keys())[0])

        self._tag = None
        self._uid = uid if uid is not None else uuid4().hex
        self._shouldBeShown = True
        self._shouldBeShownFilterFunction = shouldBeShownFilterFunction if shouldBeShownFilterFunction is not None else lambda exp: True
        self._parentGroup = None
        self._experiment = None
        self._jumptext = None
        self._isJumpable = False
        self._title = None
        self._subtitle = None
        self._statustext = None
        self._hasBeenShown = False
        self._hasBeenHidden = False

        if tag is not None:
            self.tag = tag

        if tagAndUid and (tag or uid):
            raise ValueError('tagAndUid cannot be set together with tag or uid!')

        if tagAndUid is not None:
            self.tag = tagAndUid
            self._uid = tagAndUid

        if jumptext is not None:
            self.jumptext = jumptext

        self.isJumpable = isJumpable

        if title is not None:
            self.title = title

        if subtitle is not None:
            self.subtitle = subtitle

        if statustext is not None:
            self.statustext = statustext

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, tag):
        if not (tag is None or isinstance(tag, str) or isinstance(tag, str)):
            raise TypeError("tag must be an instance of str or unicode")
        if self._tag is not None:
            raise ValueError("you're not allowed to change a tag.")
        self._tag = tag

    @property
    def uid(self):
        return self._uid

    def setShouldBeShownFilterFunction(self, f):
        """
        Sets a filter function. f must take Experiment as parameter
        :type f: function
        """
        self._shouldBeShownFilterFunction = f

    def removeShouldBeShownFilterFunction(self):
        """
        remove the filter function
        """
        self._shouldBeShownFilterFunction = lambda exp: True

    @property
    def shouldBeShown(self):
        """
        Returns True if shouldBeShown is set to True (default) and all shouldBeShownFilterFunctions return True.
        Otherwise False is returned
        """
        return self._shouldBeShown and self._shouldBeShownFilterFunction(self._experiment)

    @shouldBeShown.setter
    def shouldBeShown(self, b):
        """
        sets shouldBeShown to b.

        :type b: bool
        """
        if not isinstance(b, bool):
            raise TypeError("shouldBeShown must be an instance of bool")
        self._shouldBeShown = b

    @property
    def data(self):
        data = {'tag': self.tag,
                'uid': self.uid}

        return data

    @property
    def isJumpable(self):
        return self._isJumpable and self.jumptext is not None

    @isJumpable.setter
    def isJumpable(self, isJumpable):
        if not isinstance(isJumpable, bool):
            raise TypeError
        self._isJumpable = isJumpable

    @property
    def jumptext(self):
        return self._jumptext

    @jumptext.setter
    def jumptext(self, jumptext):
        if not (isinstance(jumptext, str) or isinstance(jumptext, str)):
            raise TypeError("jumptext must be an instance of str or unicode")
        self._jumptext = jumptext

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def subtitle(self):
        return self._subtitle

    @subtitle.setter
    def subtitle(self, subtitle):
        self._subtitle = subtitle

    @property
    def statustext(self):
        return self._statustext

    @statustext.setter
    def statustext(self, title):
        self._statustext = title

    def addedToExperiment(self, exp):
        self._experiment = exp

    def addedToQuestionGroup(self, group):
        self._parentGroup = group

    def allowLeaving(self, direction):
        return True


class Direction(object):
    UNKNOWN = 0
    FORWARD = 1
    BACKWARD = 2
    JUMP = 3

    @staticmethod
    def to_str(direction):
        if direction == Direction.UNKNOWN:
            return u"unknown"
        elif direction == Direction.FORWARD:
            return u"forward"
        elif direction == Direction.BACKWARD:
            return u"backward"
        elif direction == Direction.JUMP:
            return u"jump"
        else:
            raise ValueError("Unexpected Value")


def package_path():
    '''
    DEPRECATED

    use alfred.settings.package_path instead
    '''

    root = __file__
    if os.path.islink(root):
        root = os.path.realpath(root)
    return os.path.dirname(os.path.abspath(root))
