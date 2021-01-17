# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""

from . import element as elm
from ._core import ExpMember
from .page import PageCore, UnlinkedDataPage, DefaultFinalPage
from .exceptions import MoveError, AlfredError
from . import alfredlog
from random import shuffle

class Section(ExpMember):

    allow_forward: bool = True
    allow_backward: bool = True
    allow_jumpfrom: bool = True
    allow_jumpto: bool = True

    shuffle: bool = False

    def __init__(self, title: str = None, name: str = None, **kwargs):
        super().__init__(title=title, name=name, **kwargs)

        self.members = {}
        self._should_be_shown = True
        
        #: bool: Boolean flag, indicating whether the experiment session
        #: is currently operating within this section
        self.active: bool = False

        if kwargs.get("shuffle", None):
            self.shuffle = kwargs.get("shuffle", False)
    
    def __contains__(self, member):
        try:
            return member.name in self.all_members or member.name in self.all_elements
        except AttributeError:
            return member in self.all_members or member in self.all_elements

    def __repr__(self):
        return f"Section(class='{type(self).__name__}', name='{self.name}')"

    def __iadd__(self, other):
        self.append(other)
        return self
    
    def __getitem__(self, name):
        return self.all_members[name]
    
    def __getattr__(self, name):
        try:
            return self.all_members[name]
        except KeyError:
            return AttributeError(f"{self} has no attribute '{name}'.")

    def shuffle_members(self):
        """Non-recursive shuffling of this section's members."""

        members = list(self.members.items())
        shuffle(members)
        self.members = dict(members)
    
    @property
    def all_updated_members(self) -> dict:
        """ 
        Returns a dict of all members that already have exp access.
        """
        return {name: m for name, m in self.all_members.items() if m.exp is not None}
    
    @property
    def all_updated_pages(self) -> dict:
        pages = {}
        for name, member in self.all_updated_members.items():
            if isinstance(member, PageCore):
                pages[name] = member
        
        return pages
    
    @property
    def all_updated_elements(self) -> dict:
        elements = {}
        for page in self.all_updated_pages.values():
            elements.update(page.updated_elements)
        return elements

    @property
    def all_members(self) -> dict:
        """Returns a flat dict of all members in this section and its subsections.

        The order is preserved, i.e. members are listed in this dict in 
        the same order in which they appear in the experiment.
        """
        members = {}

        for name, member in self.members.items():
            members[name] = member
            if isinstance(member, Section):
                members.update(member.all_members)
        
        return members

    @property
    def last_member(self):
        return list(self.members.values())[-1]
    
    @property
    def first_member(self):
        return list(self.members.values())[0]

    @property
    def all_subsections(self) -> dict:
        """Returns a flat dict of all sections in this section and its subsections.

        The order is preserved, i.e. sections are listed in this dict in 
        the same order in which they appear in the experiment.
        """
        subsections = {}

        for name, member in self.members.items():
            if isinstance(member, Section):
                subsections[name] = member
                subsections.update(member.all_subsections)
        
        return subsections

    @property
    def subsections(self) -> dict:
        """Returns a flat dict of all subsections in this section.

        Subsections in subsections are not included. Use 
        :attr:`.all_subsections` for that purpose.
        """
        return {name: sec for name, sec in self.members.items() if isinstance(sec, Section)}

    @property
    def all_pages(self) -> dict:
        """Returns a flat dict of all pages in this section and its subsections.

        The order is preserved, i.e. pages are listed in this dict in 
        the same order in which they appear in the experiment.
        """

        pages = {}
        for name, member in self.members.items():
            if isinstance(member, PageCore):
                pages[name] = member
            elif isinstance(member, Section):
                pages.update(member.all_pages)
        
        return pages
    
    @property
    def all_closed_pages(self) -> dict:
        return {name: page for name, page in self.all_pages.items() if page.is_closed}
    
    @property
    def all_shown_pages(self) -> dict:
        return {name: page for name, page in self.all_pages.items() if page.has_been_shown}
    
    @property
    def pages(self) -> dict:
        """Returns a flat dict of all pages in this section.

        Pages in subsections are not included. Use :attr:`.all_pages`
        for that purpose.
        """
        return {name: page for name, page in self.members.items() if isinstance(page, PageCore)}
    
    @property
    def all_elements(self) -> dict:
        """Returns a flat dict of all elements in this section.
        
        Recursive: Includes elements from pages in this section and all 
        its subsections.
        """

        elements = {}
        for page in self.all_pages.values():
            elements.update(page.elements)
        return elements
    
    @property
    def all_input_elements(self) -> dict:
        """Returns a flat dict of all input elements in this section.
        
        Recursive: Includes elements from pages in this section and all 
        its subsections.
        """

        elements = {}
        for page in self.all_pages.values():
            elements.update(page.input_elements)
        return elements
    
    @property
    def all_shown_input_elements(self) -> dict:
        """Returns a flat dict of all shown input elements in this section.
        
        Recursive: Includes elements from pages in this section and all 
        its subsections.
        """

        elements = {}
        for page in self.all_pages.values():
            if page.has_been_shown:
                elements.update(page.input_elements)
        return elements
    
    @property
    def data(self):
        data = {}
        for page in self.all_pages.values():
            data.update(page.data)
        return data
    
    @property
    def unlinked_data(self):
        data = {}
        for page in self.all_pages.values():
            data.update(page.unlinked_data)
        
        return data
    
    @property
    def unlinked_element_data(self):
        data = {}
        for page in self.all_pages.values():
            data.update(page.unlinked_element_data)
        
        return data

    def added_to_experiment(self, exp):
        super().added_to_experiment(exp)
        self.log.add_queue_logger(self, __name__)
        self.on_exp_access()
        self.update_members_recursively()
    
    def update_members(self):
        
        for member in self.members.values():
            if not member.experiment:
                member.added_to_experiment(self.exp)
            if not member.section:
                member.added_to_section(self)
    
    def update_members_recursively(self):

        self.update_members()

        for member in self.members.values():
            member.update_members_recursively()
    
    def generate_unset_tags_in_subtree(self):
        for i, member in enumerate(self.members.values(), start=1):
            
            if member.tag is None:
                member.tag = str(i)
            
            if isinstance(member, Section):
                member.generate_unset_tags_in_subtree()

    def append_item(self, item):

        self.log.warning("Section.append_item() is deprecated. Use Section.append() instead.")

        self.append(item)

    def append_items(self, *items):

        self.log.warning("Section.append_items() is deprecated. Use Section.append() instead.")

        for item in items:
            self.append(item)

    def append(self, *items):
        for item in items:

            if item.name in dir(self):
                raise ValueError(f"Name of {item} is also an attribute of {self}.")
            
            if item.name in self.members:
                raise AlfredError(f"Name '{self.name}' is already present in the experiment.")

            item.added_to_section(self)

            self.members[item.name] = item
            
            if self.experiment is not None:
                item.added_to_experiment(self.experiment)
                item.update_members_recursively()
            
            if not item.tag:
                item.tag = str(len(self.members) + 1)


    def on_exp_access(self):
        """Hook for code that is meant to be executed as soon as a 
        section is added to an experiment.

        Example::
            class MainSection(SegmentedSection):

                def on_exp_access(self):
                    self += Page(title='Example Page')
        
        *New in v1.4.*
        """
        pass

    def on_enter(self):
        """Hook for code that is meant to be executed upon entering
        a section in an ongoing experiment.

        Example::
            class MainSection(SegmentedSection):

                def on_enter(self):
                    print("Code executed upon entering section.")

        *New in v1.4.*
        """
        pass

    def on_leave(self):
        """Hook for code that is meant to be executed upon leaving a 
        section in an ongoing experiment.

        This code will be executed *after* closing the section's last
        page.

        Example::
            class MainSection(SegmentedSection):

                def on_leave(self):
                    print("Code executed upon leaving section.")
        
        *New in v1.4.*
        """
        pass

    def on_move(self):
        pass
    
    def on_forward(self):
        pass

    def on_backward(self):
        pass

    def on_jumpfrom(self):
        pass

    def on_jumpto(self):
        pass

    def enter(self):
        self.active = True
        
        self.log.debug(f"Entering {self}.")
        self.on_enter()

        if self.shuffle:
            self.shuffle_members()

        if isinstance(self.first_member, Section) and not self.first_member.active:
            self.first_member.enter()
        
    def leave(self):
        self.log.debug(f"Leaving {self}.")
        self.on_leave()

        for page in self.all_pages.values():
            page.close()
        
        if self is self.parent.last_member:
            self.parent.leave()
    
    def resume(self):
        self.log.debug(f"Resuming to {self}.")
        self.on_resume()
    
    def hand_over(self):
        self.log.debug(f"{self} handing over to child section.")
        self.on_hand_over()
    
    def on_resume(self):
        """ 
        Hook for code to be executed on resuming this section.

        Resuming takes place, when a child section is left and the
        next page is a direct child of this section (self). Then this 
        section (self) becomes the primary current section again, it
        resumes its status.
        """
        pass

    def on_hand_over(self):
        """
        Hook for code to be executed when this section hands over.

        Handover takes place, when a subsection of this section 
        is entered.
        """
        pass

    def forward(self):
        self.on_forward()
    
    def backward(self):
        self.on_backward()
    
    def jumpfrom(self):
        self.on_jumpfrom()
    
    def jumpto(self):
        self.on_jumpto()
    
    def move(self, direction: str):
        self.on_move()
        self.update_members()

        if direction == "forward":
            self.forward()
        elif direction == "backward":
            self.backward()

    @staticmethod
    def validate(page):
        return page.validate()


class NoValidationSection(Section):
    """Section without movement restrictions.
    
    You can jump to and from this section, and inputs are not
    validated.

    """
    allow_forward: bool = True
    allow_backward: bool = True
    allow_jumpfrom: bool = True
    allow_jumpto: bool = True

    @staticmethod
    def validate(page):
        return True


class RevisitSection(Section):
    allow_forward: bool = True
    allow_backward: bool = True
    allow_jumpfrom: bool = True
    allow_jumpto: bool = True

    def forward(self):
        super().forward()
        self.exp.movement_manager.current_page.close()
    
    def jumpfrom(self):
        super().jumpfrom()
        self.exp.movement_manager.current_page.close()


class OnlyForwardSection(RevisitSection):
    allow_forward: bool = True
    allow_backward: bool = False
    allow_jumpfrom: bool = False
    allow_jumpto: bool = False


class HeadOpenSection(RevisitSection): pass


class SegmentedSection(OnlyForwardSection): pass


class FinishedSection(Section):

    allow_forward: bool = False
    allow_backward: bool = False
    allow_jumpfrom: bool = False
    allow_jumpto: bool = True

    def enter(self):
        super().enter()
        self.experiment.finish()


class RootSection(Section):

    name = "_root"

    def __init__(self, experiment):
        super().__init__()
        self._experiment = experiment
        self.log.add_queue_logger(self, __name__)
        self.content = Section(name="_content")
        self.finished_section = FinishedSection(name="__finished_section")
        self.finished_section += DefaultFinalPage(name="_final_page")

        self._all_pages_list = None
        self._all_page_names = None
    
    def append_root_sections(self):
        self += self.content
        self += self.finished_section
    
    @property
    def all_page_names(self):
        """Improvised caching mechanism for the list of all page names."""

        if not self._all_page_names:
            self._all_page_names = list(self.all_pages.keys())

        elif not len(self._all_page_names) == len(self.all_pages):
            self._all_page_names = list(self.all_pages.keys())
        
        return self._all_page_names
    
    @property
    def all_pages_list(self):
        """Improvised caching mechanism for the list of all pages."""

        if not self._all_pages_list:
            self._all_pages_list = list(self.all_pages.values())

        elif not len(self._all_pages_list) == len(self.all_pages):
            self._all_pages_list = list(self.all_pages.values())
        
        return self._all_pages_list
    
    @property
    def final_page(self):
        return self.finished_section._final_page

    @final_page.setter
    def final_page(self, page):
        page += elm.HideNavigation()
        self.finished_section.members = {}
        self.finished_section._final_page = page
    
