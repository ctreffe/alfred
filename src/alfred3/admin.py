import typing as t
from enum import Enum
from abc import ABC, abstractproperty
from functools import total_ordering

from .element.action import JumpList
from .page import Page
from .page import PasswordPage
from .section import Section
from .section import ForwardOnlySection
from .exceptions import AbortMove, AlfredError

@total_ordering
class AdminAccess(Enum):
    """
    Access levels in admin mode.

    The levels are:

    - :attr:`.LEVEL1`: Lowest clearance. Access mainly to monitoring pages.
    - :attr:`.LEVEL2`: Medium clearance. Access to moderation functionality.
    - :attr:`.LEVEL3`: Highest clearance. Required for access to critical
      operations like data deletion.
    """
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3

    def __lt__(self, other):
        if self.__class__ is other.__class__:
          return self.value < other.value
        return NotImplemented


class AdminPage(Page, ABC):

    """
    Base class for all pages to use in the admin mode.

    Admin pages must inherit from *AdminPage* and define the attribute
    :attr:`.access_level`.

    The access level must be set to one of the values defined by
    :class:`.AdminAccess`.

    See Also:
        It is most convenient to simply use one of the three admin page
        base classes:

        - :class:`.MonitoringPage` base page for 'level 1' admin pages.
        - :class:`.ModeratorPage` base page for 'level 2' admin pages.
        - :class:`.ManagerPage` base page for 'level 3' admin pages.

    Examples:

        ::
            import alfred3 as al
            from alfred3.page import AdminPage, AdminAccess

            class MyAdminPage(AdminPage):
                access_level = AdminAccess.LEVEL1

                def on_exp_access(self):
                    self += al.Text("My text")

    """
    
    @abstractproperty
    def access_level(self):
        """
        Returns the access level that is needed to view this page in
        the admin mode.
        """
        pass


    def _on_showing_widget(self, show_time):
        if not self.access_level <= self.exp.content.access_level:
            raise AbortMove
        
        if not self._has_been_shown:
            name = self.name + "__admin_jumplist__"
            jumplist = JumpList(
                scope="admin_content",
                check_jumpto=False,
                check_jumpfrom=False,
                name=name,
                debugmode=True,
                display_page_name=False
            )
            jumplist.should_be_shown = False
            self += jumplist
        super()._on_showing_widget(show_time)
        

class MonitoringPage(AdminPage):
    access_level = AdminAccess.LEVEL1


class ModeratorPage(AdminPage):
    access_level = AdminAccess.LEVEL2


class ManagerPage(AdminPage):
    access_level = AdminAccess.LEVEL3


class _AuthPage(PasswordPage):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_members = None

    def custom_move(self):
        # this whole function should move to a Section.on_leave or
        # Page.on_first_hide hook when possible

        # this is a hotfix, because Section.on_leave and Page.on_first_hife
        # currently do not allow adding pages directly behind the current
        # one on moving forward
        if not self._validate_elements():
            
            # prevent double match hint
            [m for m in self.pw.hint_manager.get_messages()]
            return True

        admin_content = Section(name="admin_content")
        for member in self.admin_members.values():

            # exp.content is the admin section in admin mode
            if member.access_level <= self.exp.content.access_level:
                admin_content += member
        
        self.exp += admin_content
        self.admin_members = None

        return True


class _AdminSection(Section):

    def added_to_experiment(self, exp):

        auth_section = ForwardOnlySection(name="admin_auth")

        self.passwords = self.process_passwords(exp)

        auth_section += _AuthPage(
            password=self.password_list, 
            name="_admin_auth_page_", 
            title="alfred3 Admin Mode"
        )
        self += auth_section
        super().added_to_experiment(exp)

    def process_passwords(self, exp) -> t.Dict[str, list]:
        pw1 = exp.secrets.get("general", "adminpass_lvl1")
        pw2 = exp.secrets.get("general", "adminpass_lvl2")
        pw3 = exp.secrets.get("general", "adminpass_lvl3")

        pws = {}
        pws["lvl1"] = pw1.split("|")
        pws["lvl2"] = pw2.split("|")
        pws["lvl3"] = pw3.split("|")

        self.validate_passwords(pws)
        return pws
    
    @property
    def password_list(self) -> t.List[str]:
        pws = self.passwords
        return pws["lvl1"] + pws["lvl2"] + pws["lvl3"]
    
    @staticmethod
    def validate_passwords(passwords):
        missing_passwords = []
        for lvl in ["lvl1", "lvl2", "lvl3"]:
            pw = passwords[lvl]
            if (len(pw) == 1 and pw[0] == "") or not pw:
                missing_passwords.append(lvl)
        
        if missing_passwords:
            raise AlfredError(f"To activate the admin mode, you must define passwords for all three levels in secrets.conf. Passwords are missing for levels: {', '.join(missing_passwords)}.")

        comparisons = []
        for pw1 in passwords["lvl1"]:
            comparisons += [pw1 == pw2 for pw2 in passwords["lvl2"]]
            comparisons += [pw1 == pw3 for pw3 in passwords["lvl3"]]

        for pw2 in passwords["lvl2"]:
            comparisons += [pw2 == pw3 for pw3 in passwords["lvl3"]]

        if any(comparisons):
            raise AlfredError(
                (
                    "Two equal passwords for two different admin levels found."
                    " Passwords must be unique to a level. Please change one of the passwords."
                )
            )

    @property
    def access_level(self) -> int:
        """
        Returns the level of admin access based on the password that
        was entered on admin authentication.
        """
        pw = self.exp.values.get("pw")

        if pw in self.passwords["lvl1"]:
            return AdminAccess.LEVEL1
        elif pw in self.passwords["lvl2"]:
            return AdminAccess.LEVEL2
        elif pw in self.passwords["lvl3"]:
            return AdminAccess.LEVEL3
        else:
            raise AlfredError("Invalid password.")

