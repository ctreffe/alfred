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
from ._helper import check_name
from .exceptions import AlfredError


class ExpMember:
    name: str = None
    instance_level_logging: bool = False

    def __init__(
        self,
        name: str = None,
        title=None,
        subtitle=None,
        statustext=None,
        showif: dict = None,
    ):

        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)

        self.showif = showif if showif else {}
        self._should_be_shown = True

        self._experiment = None
        self._parent_section = None
        self._section = None
        
        self._title = None
        self._subtitle = None
        self._statustext = None
        self._has_been_shown = False
        self._has_been_hidden = False


        # the following assignments allow for assignment via class variables
        # during subclasses, but override the attributes, if given as
        # init parameters
        if title is not None:
            self.title = title

        if subtitle is not None:
            self.subtitle = subtitle

        if statustext is not None:
            self.statustext = statustext
        
        if name is not None:
            self.name = name
        
        # regardless of how name was assigned, check it
        if self.name is not None:
            check_name(self.name)
            self._uid = self.name
            self._tag = self.name
        elif self.name is None:
            self._uid = uuid4().hex
            self.name = self.uid
            self._tag = None
        
        self._name_at_init = self.name


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
        return self._should_be_shown

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
        self._experiment = exp
        self.log.add_queue_logger(self, __name__)

        if self.name in self.experiment.root_section.all_members:
            raise AlfredError(f"Name '{self.name}' is already present in the experiment.")

        if self.name != self._name_at_init:
            raise AlfredError(f"{self}: Name must not be changed after assignment.")

        if self.name in exp.__dict__:
            raise ValueError(
                (
                    "The experiment has an attribute of the same name as"
                    f"the page '{self}'. Please choose a different page name."
                )
            )

    @property
    def experiment(self):
        return self._experiment
    
    @property
    def exp(self):
        return self._experiment

    def added_to_section(self, section):
        self._parent_section = section
        self._section = section

    @property
    def section(self):
        return self._section

    @property
    def parent(self):
        return self._parent_section

    @property
    def tree(self):
        if not self.parent:
            return self.tag

        if self.parent.tree:
            return self.parent.tree + "." + self.tag
        else:
            return self.tag

    @property
    def short_tree(self):
        return self.tree.replace("root_", "")

    def allow_leaving(self, direction):
        return True

