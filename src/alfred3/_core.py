# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""


from builtins import object
import os.path
import logging
import re
from uuid import uuid4
from typing import List

from . import alfredlog
from ._helper import check_name
from ._helper import _DictObj
from .exceptions import AlfredError


class ExpMember:
    """
    Baseclass for sections and pages.

    Args:
        name (str): Name of the member. Must be unique throughout the
            experiment. Can be defined as a class attribute. When you
            write a page or section in *class style*, the name can be
            inferred from the class name and does not need to be
            defined explicitly again. If a name is defined explicitly
            as a class attribute, that name is used.
        title (str): Title of the member. Can be defined as a class 
            attribute.
        subtitle (str): Subtitle of the member. Can be defined as a 
            class attribute.
        vargs (dict): A dictionary that can be used to pass additional
            arguments to the page. The arguments are then available as
            an instance attribute. As a special feature, the instance
            attribute allows you to access the values of the dictionary
            not only via the usual square-bracket notation, but also
            via dot-notation. 

            This argument fulfills a similar function as ``**kwargs`` do
            sometimes, but it makes sure that user-defined additional
            arguments will not collide with inherited keywords arguments.
            
            Can be defined as a class attribute.
    """


    #: Unique name of the member.
    name: str = None

    #: If *True*, the member will spawn a logger that can be configured
    #: individually for each instance
    instance_log: bool = False

    #: Name of the parent section. Used when a member is appended to 
    #: the :class:`.Experiment`. If *None*, a member will be appended
    #: to the "_content" section.
    parent_name = None

    def __init__(
        self,
        name: str = None,
        title: str = None,
        subtitle: str = None,
        vargs: dict = None,
    ):

        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)
        
        self._should_be_shown = True

        self._experiment = None
        self._parent_section = None
        self._section = None
        
        self._title = None
        self._subtitle = None
        self._has_been_shown = False
        self._has_been_hidden = False

        # the following assignments allow for assignment via class variables
        # during subclasses, but override the attributes, if given as
        # init parameters
        self._vargs = _DictObj()
        if vargs is not None:
            self._vargs = _DictObj(vargs)
        elif self.vargs:
            self.vargs = _DictObj(self.vargs)

        if title is not None:
            self.title = title

        if subtitle is not None:
            self.subtitle = subtitle

        self._name_set_via = {}

        if name is not None:
            self._set_name(name, via="argument")
        elif self.name is not None:
            self._set_name(self.name, via="class")
        
        if self.name is None:
            raise ValueError(f"{type(self).__name__} must be named!")
    
    @property
    def vargs(self) -> dict:
        """
        A dictionary of additional arguments passed on the class upon
        initialization. Can be defined as a class attribute.

        As a special feature, you can use dot notation to access
        (but not to set) values on this dictionary.

        Examples:

            Example of definig the *vargs* as a class attribute on a page::

                import alfred3 as al
                exp = al.Experiment()

                @exp.member
                class Demo(al.Page):
                    vargs = {"variable_argument": "demo"}

                    def on_exp_access(self):
                        self += al.Text(self.vargs.variable_argument)
            
            Example of using the *vargs* in page instantiation::

                import alfred3 as al
                exp = al.Experiment()

                class TestPage(al.Page):
                    def on_exp_access(self):
                        self += al.Text(f"{self.vargs.test}")

                @exp.member
                class Test(al.Section):

                    def on_exp_access(self):
                        for i in range(3):
                            self += TestPage(name=f"p{i}", vargs={"test": 123})

        """
        return self._vargs
        
        
    def _set_name(self, name: str, via: str):
        """
        Helps organize the different ways a name can be set.

        The ways are:

        1. As a class variable when deriving a page as a new class
        2. As an init argument when instantiating a class

        If a name was set via class variable, the init argument 
        can override it.

        """

        check_name(name)
        self._uid = name
        self._tag = name
        self.name = name
        self._name_set_via[via] = self.name

        if len(self._name_set_via) > 1:
            msg = f"Name of {self} was set via multiple methods. Current winner: '{self.name}', set via {via}."
            self.log.debug(msg)
    
    def showif(self) -> bool:
        """
        Hook for controlling whether a page or section should be shown.

        The showif hook is used by overloading. Inside the hook, you
        have access to the current experiment session via ``self.exp``.

        Examples:
            In this examples, the second page is shown only if "yes"
            was entered on the first page::

                import alfred3 as al
                exp = al.Experiment()


                @exp.member
                class Hello(al.Page):
                    def on_exp_access(self):
                        self += al.TextEntry(leftlab="Show second page?", name="el1")


                @exp.member
                class ShowPage(al.Page):
                    title = "Showif Page"
                    
                    def showif(self):
                        return self.exp.values.get("el1") == "yes"
                
            In this example, the "Main" section is shown only if "yes"
            was entered on the first page::

                import alfred3 as al
                exp = al.Experiment()


                @exp.member
                class Hello(al.Page):
                    def on_exp_access(self):
                        self += al.TextEntry(leftlab="Show second page?", name="el1")


                @exp.member
                class Main(al.Section):

                    def showif(self):
                        return self.exp.values.get("el1") == "yes"
                    
                    def on_exp_access(self):
                        self += al.Page(title="Showif Section Page 1", name="showif_page1")
                        self += al.Page(title="Showif Section Page 2", name="showif_page2")

        """
        return True
        
    
    @property
    def all_input_elements(self) -> dict:
        """
        Redefined by pages and section.
        """
        return {}

    @property
    def tag(self) -> str:
        """
        Alias for :attr:`.name`, included under this name for backwards
        compatibility. For new code, use *name*.
        """
        return self._tag

    @tag.setter
    def tag(self, tag):
        if not (tag is None or isinstance(tag, str) or isinstance(tag, str)):
            raise TypeError("tag must be an instance of str or unicode")
        if self._tag is not None:
            raise ValueError("you're not allowed to change a tag.")
        self._tag = tag

    @property
    def uid(self) -> str:
        """
        Alias for :attr:`.name`, included under this name for backwards
        compatibility. For new code, use *name*.
        """
        return self._uid
    
    def visible(self, attr: str) -> dict:
        """
        Returns the subset of members in the given attribute that should
        be shown.
        
        Args:
            attr (str): Name of an attribute of the class which returns
                a dictionary of members. For instance, sections allow
                'all_members', 'members', 'all_pages', 'pages', and 
                pages allow 'elements', 'all_elements', 'input_elements',
                'filled_input_elements'.
        """
        d = getattr(self, attr)
        return {name: value for name, value in d.items() if value.should_be_shown}

    @property
    def should_be_shown(self) -> bool:
        """
        bool: Returns True if should_be_shown is set to True (default) and all
        showif conditions return True.
        """
        cond1 = self._should_be_shown
        cond2 = self.showif()
        return cond1 and cond2

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
    def title(self) -> str:
        """
        Page title (str).
        """
        if self._title is not None:
            return self._title
        else:
            return ""

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def subtitle(self) -> str:
        """
        Page subtitle (str).
        """
        return self._subtitle

    @subtitle.setter
    def subtitle(self, subtitle):
        self._subtitle = subtitle

    def added_to_experiment(self, exp):
        """
        Informs the member that it was added to an experiment session.

        After this method is called, the member has access to the
        experiment session through the attribute :attr:`.exp`
        """
        if not self.name:
            raise AlfredError(f"{type(self).__name__} must have a unique name.")
        self._check_name_uniqueness(exp)
        self._experiment = exp

    def _check_name_uniqueness(self, exp):

        if self.name in exp.root_section.all_updated_members:
            raise AlfredError(f"Name '{self.name}' is already present in the experiment.")

        # if self.name != list(self._name_set_via.values())[-1]:
        #     raise AlfredError(f"{self}: Name must not be changed after assignment.")

        if self.name in dir(exp):
            raise ValueError(
                (
                    "The experiment has an attribute of the same name as"
                    f"the page '{self}'. Please choose a different page name."
                )
            )
    
    @property
    def experiment(self):
        """
        The :class:`.ExperimentSession` to which this member belongs.
        """
        return self._experiment
    
    @property
    def exp(self):
        """
        The :class:`.ExperimentSession` to which this member belongs.
        """
        return self._experiment
    
    @exp.setter
    def exp(self, value):
        self._experiment = value
    
    @experiment.setter
    def experiment(self, value):
        self._experiment = value

    def added_to_section(self, section):
        """
        Informs the member that it was added to a section.
        """
        self._parent_section = section
        self._section = section

    @property
    def section(self):
        """
        The member's parent section.
        """
        return self._section
    
    @section.setter
    def section(self, section):
        if section is self._section:
            self._section = section
        else:
            raise ValueError("Cannot change a member's section.")

    @property
    def parent(self):
        """
        Alias for :attr:`.section`.
        """
        return self._parent_section
    
    def uptree(self) -> list:
        """
        List of the parent section and the grandparent sections (recursive).
        """
        out = []
        if self.parent:
            out += [self.parent]
            out += self.parent.uptree()
            return out
        else:
            return out

    @property
    def tree(self) -> str:
        """
        A single string, indicating the member's position in the experiment.
        Consist of the names of the parent section and all grandparent
        sections, separated by dots.
        """
        if not self.parent:
            return self.tag

        if self.parent.tree:
            return self.parent.tree + "." + self.tag
        else:
            return self.tag

    @property
    def short_tree(self) -> str:
        """
        Short version of :attr:`.tree`, without the ``_root._content``
        part that is the same for all members.
        """
        return self.tree.replace("_root._content.", "")
    
    def position_in_section(self) -> int:
        """
        Returns the position of this page or section inside its parent 
        section, starting at 1.

        .. versionadded:: 2.3.0
        """
        members = [m.name for m in self.section.members.values()]
        return members.index(self.name) + 1
    

    def __str__(self):
        return f"{type(self).__name__}(name='{self.name}')"

    def __repr__(self):
        return self.__str__()

