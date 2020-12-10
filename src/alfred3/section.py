# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""

from deprecation import deprecated

from . import element as elm
from . import element_responsive as relm
from ._core import ExpMember
from .page import PageCore, HeadOpenSectionCantClose, UnlinkedDataPage, DefaultFinalPage
from .exceptions import MoveError, AlfredError
from . import alfredlog
from random import shuffle

class Section(ExpMember):

    allow_forward: bool = True
    allow_backward: bool = True
    allow_jumpfrom: bool = True
    allow_jumpto: bool = True

    shuffle: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.members = {}
        self._should_be_shown = True

        if kwargs.get("shuffle", None):
            self.shuffle = kwargs.get("shuffle", False)

    def __str__(self):
        section_class = type(self).__name__
        m = ", ".join([f"{type(m).__name__}(name='{m.name}')" for m in self.members.values()])
        return f"{section_class}(name='{self.name}', parent='{self.parent.name}', members=[{m}])"

    def __iadd__(self, other):
        self.append(other)
        return self

    def shuffle_members(self):
        """Non-recursive shuffling of this section's members."""

        members = list(self.members.items())
        shuffle(members)
        self.members = dict(members)

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
        return {name: page for name, page in self.all_pages if page.is_closed}
    
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
    def all_filled_input_elements(self) -> dict:
        """Returns a flat dict of all filled input elements in this section.
        
        Recursive: Includes elements from pages in this section and all 
        its subsections.
        """

        elements = {}
        for page in self.all_pages.values():
            elements.update(page.filled_input_elements)
        return elements

    @property
    def data(self):
        data = super(Section, self).data
        data["subtree_data"] = []
        for q_core in self.members.values():
            if isinstance(q_core, UnlinkedDataPage):
                continue
            data["subtree_data"].append(q_core.data)

        return data
    
    def unlinked_data(self, encrypt):
        data = {"tag": self.tag}
        data["subtree_data"] = []
        for member in self.members.values():
            if isinstance(member, UnlinkedDataPage):
                data["subtree_data"].append(member.unlinked_data(encrypt=encrypt))

        return data

    def unlinked_data_present(self):
        """Returns *True*, if unlinked data was collected during the
        experiment and *False*, if no unlinked data was collected.
        """
        present = False
        for member in self.members.values():
            if isinstance(member, UnlinkedDataPage):
                present = True
            elif isinstance(member, Section):
                present = member.unlinked_data_present()

        return present

    @property
    def codebook_data(self):
        data = {}
        for page in self.all_pages.values():
            data.update(page.codebook_data)
        return data

    def added_to_experiment(self, exp):
        super().added_to_experiment(exp)
        
        for member in self.members.values():
            member.added_to_experiment(exp)

        self.on_exp_access()

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
            
            try:
                if hasattr(self, item.uid):
                    raise ValueError((f"Uid of {item} is also an attribute of {self}." 
                "Please choose a different uid."))
            except KeyError:
                pass
            
            if self.experiment is not None:
                item.added_to_experiment(self.experiment)
            
            self.members[item.name] = item
            item.added_to_section(self)
            self.generate_unset_tags_in_subtree()

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
        self.on_enter()
        self.on_move()

        if self.shuffle:
            self.shuffle_members()

        if isinstance(self.first_member, Section):
            self.first_member.enter()
    
    def leave(self):
        self.on_move()
        self.on_leave()
        for page in self.all_pages.values():
            page.close()
        
        if self is self.parent.last_member:
            self.parent.leave()

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

        if direction == "forward":
            self.forward()
        elif direction == "backward":
            self.backward()
        elif direction == "jumpfrom":
            self.jumpfrom()
        elif direction == "jumpto":
            self.jumpto()

    def allow_move(self, direction: str):
        
        direction_allowed = getattr(self, "allow_" + direction)
        current_page = self.exp.movement_manager.current_page
        page_validate = current_page.allow_leaving(direction=direction)

        return direction_allowed and page_validate


class NoValidationSection(Section):
    """Section without movement restrictions.
    
    You can jump to and from this section, and inputs are not
    validated.

    """
    allow_forward: bool = True
    allow_backward: bool = True
    allow_jumpfrom: bool = True
    allow_jumpto: bool = True

    def allow_move(self, direction: str):
        direction_allowed = getattr(self, "allow_" + direction)
        return direction_allowed


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

        self.content_section = Section(name="_content")
        self.finished_section = FinishedSection(name="_finished_section")
        self.final_page = DefaultFinalPage()

        self._all_pages_list = None
    
    @property
    def all_pages_list(self):
        """Improvised caching mechanism for the list of all pages."""

        if not self._all_pages_list:
            self._all_pages_list = list(self.all_pages.values())

        elif not len(self._all_pages_list) == len(self.all_pages):
            self._all_pages_list = list(self.all_pages.values())
        
        return self._all_pages_list

    def on_enter(self):
        self.finished_section += self._final_page
        
        self += self.content_section
        self += self.finished_section
    
    @property
    def final_page(self):
        return self._final_page

    @final_page.setter
    def final_page(self, page):
        self._final_page = page
        self._final_page += relm.HideNavigation()
        self.finished_section.members = {page.name: page}
    
    @deprecated("1.5", "2.0", None, details="Use the simple setter for the attribute 'final_page' instead.")
    def append_item_to_finish_section(self, item):
        """
        :param item: Element vom Typ Page oder Section

        .. todo:: Ist diese Funktion überhaupt nötig, wenn die finishedSection in init bereits erstellt wird?
        """
        self.final_page = item
