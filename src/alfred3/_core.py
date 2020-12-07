# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""


from builtins import object
import os.path
import logging
import re
from uuid import uuid4

from . import alfredlog


class ContentCore(object):
    name: str = None

    def __init__(
        self,
        name=None,
        is_jumpable=True,
        jumptext=None,
        title=None,
        subtitle=None,
        statustext=None,
        should_be_shown_filter_function=None,
        instance_level_logging=False,
        **kwargs,
    ):

        if kwargs != {}:
            raise ValueError("parameter '%s' is not supported." % list(kwargs.keys())[0])

        self._tag = None
        self._uid = uuid4().hex
        self.instance_level_logging = instance_level_logging
        self._should_be_shown = True
        self._should_be_shown_filter_function = (
            should_be_shown_filter_function
            if should_be_shown_filter_function is not None
            else lambda exp: True
        )
        self._parent_group = None
        self._experiment = None
        self._jumptext = None
        self._is_jumpable = False
        self._title = None
        self._subtitle = None
        self._statustext = None
        self._has_been_shown = False
        self._has_been_hidden = False

        if jumptext is not None:
            self.jumptext = jumptext

        self.is_jumpable = is_jumpable

        if title is not None:
            self.title = title

        if subtitle is not None:
            self.subtitle = subtitle

        if statustext is not None:
            self.statustext = statustext

        if name is not None:
            if re.match(pattern=r"^[a-zA-z](\d|_|[a-zA-Z])*$", string=name):
                self.name = name
            else:
                raise ValueError(
                    (
                        "Name must start with a letter and can include only"
                        "letters (a-z, A-Z), digits (0-9), and underscores ('_')."
                    )
                )

        if self.name is not None:
            self._uid = self.name
            self._tag = self.name

    def get_page_data(self, page_uid=None):
        data = self._experiment.data_manager.find_experiment_data_by_uid(page_uid)
        return data

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

    def set_should_be_shown_filter_function(self, f):
        """
        Sets a filter function. f must take Experiment as parameter
        :type f: function
        """
        self._should_be_shown_filter_function = f

    def remove_should_be_shown_filter_function(self):
        """
        remove the filter function
        """
        self._should_be_shown_filter_function = lambda exp: True

    @property
    def should_be_shown(self):
        """
        Returns True if should_be_shown is set to True (default) and all should_be_shown_filter_functions return True.
        Otherwise False is returned
        """
        return self._should_be_shown and self._should_be_shown_filter_function(self._experiment)

    @should_be_shown.setter
    def should_be_shown(self, b):
        """
        sets should_be_shown to b.

        :type b: bool
        """
        if not isinstance(b, bool):
            raise TypeError("should_be_shown must be an instance of bool")
        self._should_be_shown = b

    @property
    def data(self):
        data = {"tag": self.tag, "uid": self.uid}

        return data

    @property
    def is_jumpable(self):
        return self._is_jumpable and self.jumptext is not None

    @is_jumpable.setter
    def is_jumpable(self, is_jumpable):
        if not isinstance(is_jumpable, bool):
            raise TypeError
        self._is_jumpable = is_jumpable

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

    def added_to_experiment(self, exp):
        if self.name is not None and self.name in exp.page_controller.all_members_dict:
            raise ValueError(f"A section or page of name '{self.name}' already exists.")
        
        self._experiment = exp


    @property
    def experiment(self):
        return self._experiment

    def added_to_section(self, group):
        self._parent_group = group
        self._section = group

    @property
    def section(self):
        return self._section

    @property
    def parent(self):
        return self._parent_group

    @property
    def tree(self):
        if not self.parent:
            return self.tag

        if self.parent.tree:
            return self.parent.tree + "_" + self.tag
        else:
            return self.tag

    @property
    def short_tree(self):
        return self.tree.replace("rootSection_", "")

    def allow_leaving(self, direction):
        return True


class Direction(object):
    UNKNOWN = 0
    FORWARD = 1
    BACKWARD = 2
    JUMP = 3

    @staticmethod
    def to_str(direction):
        if direction == Direction.UNKNOWN:
            return "unknown"
        elif direction == Direction.FORWARD:
            return "forward"
        elif direction == Direction.BACKWARD:
            return "backward"
        elif direction == Direction.JUMP:
            return "jump"
        else:
            raise ValueError("Unexpected Value")


def package_path():
    """
    DEPRECATED

    use alfred.settings.package_path instead
    """

    root = __file__
    if os.path.islink(root):
        root = os.path.realpath(root)
    return os.path.dirname(os.path.abspath(root))
