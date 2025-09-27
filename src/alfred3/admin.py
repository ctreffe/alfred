"""
Functionality associated with alfred3's admin mode.
"""

from abc import ABC, abstractproperty
from enum import Enum
from functools import total_ordering

from jinja2 import Template

from ._helper import inherit_kwargs
from .element.action import JumpList
from .element.core import Element
from .element.display import Text, VerticalSpace
from .element.misc import WebExitEnabler
from .exceptions import AbortMove, AlfredError
from .page import Page, PasswordPage
from .section import ForwardOnlySection, Section


@total_ordering
class AdminAccess(Enum):
    """
    Access levels in admin mode.

    The levels are:

    - :attr:`.LEVEL1`: Lowest clearance. This level should be granted to
      pages that display additional information but do not allow active
      intervention. Used by :class:`.SpectatorPage`.
    - :attr:`.LEVEL2`: Medium clearance. This level should be granted to
      pages that allow non-critical actions like exporting data or sending
      emails.
    - :attr:`.LEVEL3`: Highest clearance. This level should be granted to
      pages that allow the most critical actions, e.g. permanent data
      deletion. As a rule of thumb, only one person should have level 3
      access for an experiment.

    If you use the admin mode, you always have to specify passwords for
    all three levels in *secrets.conf*, section *general*::

        # secrets.conf
        [general]
        adminpass_lvl1 = demo
        adminpass_lvl2 = use - better - passwords
        adminpass_lvl3 = to - protect - access

    You can specficy multiple passwords for the same level to enable
    a token-like authentication management. To specifiy multiple passwords,
    simply separate them by ``|``::

        # secrets.conf
        [general]
        adminpass_lvl1 = demo | demopass - 2
        adminpass_lvl2 = use - better - passwords
        adminpass_lvl3 = to - protect - access


    .. note:: Because of its special meaning for the separation of multiple
        passwords, the character ``|`` cannot be part of a password.

    """

    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


@inherit_kwargs
class AdminPage(Page, ABC):
    """
    Base class for all pages to use in the admin mode.

    Args:
        {kwargs}

    Notes:
        Admin pages must inherit from *AdminPage* and define the attribute
        :attr:`.access_level`.

        The access level must be set to one of the values defined by
        :class:`.AdminAccess`.

    See Also:
        It is most convenient to simply use one of the three admin page
        base classes:

        - :class:`.SpectatorPage` base page for 'level 1' admin pages.
        - :class:`.OperatorPage` base page for 'level 2' admin pages.
        - :class:`.ManagerPage` base page for 'level 3' admin pages.

    Examples:

        In this example, we define a new admin page with access level 1::
            import alfred3 as al
            from alfred3.page import AdminPage, AdminAccess


            class MyAdminPage(AdminPage):
                access_level = AdminAccess.LEVEL1

                def on_exp_access(self):
                    self += al.Text("My text")

    """

    responsive_width = "85%, 75%, 75%, 70%"

    def added_to_experiment(self, experiment):
        self += Text(
            f"{experiment.content.access_level}", align="center", font_size="small"
        )
        super().added_to_experiment(experiment)

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
            self += WebExitEnabler()
            name = self.name + "__admin_jumplist__"
            jumplist = JumpList(
                scope="admin_content",
                check_jumpto=False,
                check_jumpfrom=False,
                name=name,
                debugmode=True,
                display_page_name=False,
            )
            jumplist.should_be_shown = False
            self += jumplist
        super()._on_showing_widget(show_time)


@inherit_kwargs
class SpectatorPage(AdminPage):
    """
    Base class for admin pages with spectator access.

    Args:
        {kwargs}

    A SpectatorPage has access level :class:`.AdminAccess.LEVEL1`
    This means that it can be accessed with the password defined
    by the option *adminpass_lvl1* in section *general* of *secrets.conf*

    The base class is intended to be used for the definition of specific
    admin pages.

    See Also:
        The individual levels are described in :class:`.AdminAccess`. If
        you are uncertain about the correct level for your admin page,
        check this page out.

    Examples:
        A basic admin page that shows the number of datasets associated
        with the experiment. First we define the class, then we add it
        to the experiment's admin mode. Note that the *admin* module has
        to be imported individually::

            import alfred3 as al
            from alfred3 import admin

            exp = al.Experiment()


            @exp.member(admin=True)
            class MyAdminPage(admin.SpectatorPage):
                def on_exp_access(self):
                    n = len(self.exp.all_exp_data)
                    self += al.Text(f"Number of data sets: {{n}}")

    """

    access_level = AdminAccess.LEVEL1


@inherit_kwargs
class OperatorPage(AdminPage):
    """
    Base class for admin pages with operator access.

    Args:
        {kwargs}

    A monitoring page has access level :class:`.AdminAccess.LEVEL1`
    This means that it can be accessed with the password defined
    by the option *adminpass_lvl2* in section *general* of *secrets.conf*

    The base class is intended to be used for the definition of specific
    admin pages.

    See Also:
        The individual levels are described in :class:`.AdminAccess`. If
        you are uncertain about the correct level for your admin page,
        check this page out.

    Examples:
        A basic admin page that shows the number of datasets associated
        with the experiment. First we define the class, then we add it
        to the experiment's admin mode. Note that the *admin* module has
        to be imported individually::

            import alfred3 as al
            from alfred3 import admin

            exp = al.Experiment()


            @exp.member(admin=True)
            class MyAdminPage(admin.OperatorPage):
                def on_exp_access(self):
                    n = len(self.exp.all_exp_data)
                    self += al.Text(f"Number of data sets: {{n}}")

    """

    access_level = AdminAccess.LEVEL2


@inherit_kwargs
class ManagerPage(AdminPage):
    """
    Base class for admin pages with manager access.

    Args:
        {kwargs}

    A monitoring page has access level :class:`.AdminAccess.LEVEL1`
    This means that it can be accessed with the password defined
    by the option *adminpass_lvl3* in section *general* of *secrets.conf*

    The base class is intended to be used for the definition of specific
    admin pages.

    See Also:
        The individual levels are described in :class:`.AdminAccess`. If
        you are uncertain about the correct level for your admin page,
        check this page out.

    Examples:
        A basic admin page that shows the number of datasets associated
        with the experiment. First we define the class, then we add it
        to the experiment's admin mode. Note that the *admin* module has
        to be imported individually::

            import alfred3 as al
            from alfred3 import admin

            exp = al.Experiment()


            @exp.member(admin=True)
            class MyAdminPage(admin.ManagerPage):
                def on_exp_access(self):
                    n = len(self.exp.all_exp_data)
                    self += al.Text(f"Number of data sets: {{n}}")

    """

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
            title="alfred3 Admin Mode",
        )
        self += auth_section
        super().added_to_experiment(exp)

    def process_passwords(self, exp) -> dict[str, list]:
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
    def password_list(self) -> list[str]:
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
            raise AlfredError(
                "To activate the admin mode, you must define passwords for all three"
                " levels in secrets.conf. Passwords are missing for levels:"
                f" {', '.join(missing_passwords)}."
            )

        comparisons = []
        for pw1 in passwords["lvl1"]:
            comparisons += [pw1 == pw2 for pw2 in passwords["lvl2"]]
            comparisons += [pw1 == pw3 for pw3 in passwords["lvl3"]]

        for pw2 in passwords["lvl2"]:
            comparisons += [pw2 == pw3 for pw3 in passwords["lvl3"]]

        if any(comparisons):
            raise AlfredError(
                "Two equal passwords for two different admin levels found. Passwords"
                " must be unique to a level. Please change one of the passwords."
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


DELETE_UNLINKED_HTML = """
<!-- Button trigger modal -->
<button
    type="button"
    class="btn btn-danger {{ css_class_element }}"
    data-toggle="modal"
    data-target="#{{ name }}-modal"
    id="{{ name }}"
    style="{{ fontsize }}"
    >
  <i class="fas fa-trash-alt mr-2"></i>{{ text }}
</button>

<!-- Modal -->
<div
    class="modal fade"
    id="{{ name }}-modal"
    tabindex="-1"
    aria-labelledby="{{ name}}-modal-label"
    aria-hidden="true">

  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="{{ name}}-modal-label">Delete Unlinked Data</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
      <div class="mb-3">
      This action cannot be undone!
      </div>


        <div class="form-group">
            <label for="{{ name }}-confirm">
            Enter experiment title: <b>{{ exptitle }}</b>
            </label>
            <input
                type="text"
                class="form-control"
                id="{{ name }}-confirm"
                name="{{ name }}-confirm"
                aria-describedby="deleteConfirmation"
            >

            <small id="deleteConfirmation" class="form-text text-muted">
            This is a safety measure to ensure that you do not delete data accidentally.
            </small>
        </div>

        <span id="{{ name }}-spinner" class="mr-1"></span>
        <span id="{{ name }}-feedback"></span>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
        Close
        </button>
        <button type="button" class="btn btn-danger" id="{{ name }}-delete">
        <i class="fas fa-trash-alt mr-2"></i>DELETE
        </button>

      </div>
    </div>
  </div>
</div>
"""

DELETE_UNLINKED_JS = """
$(document).ready(function() {
    $( "#{{ name }}-delete" ).click(function() {
        value = $( "#{{ name }}-confirm" ).val()
        console.log(value)

        if (value == "{{ exptitle }}") {
            $( "#{{ name }}-spinner" ).html(
                "<div class='spinner-border' role='status'>"
                + "<span class='sr-only'>Loading...</span></div>"
            )
            $.get("{{ url }}", function(data){

            setTimeout(function() {
                $( "#{{ name }}-spinner" ).html("<i class='fas fa-check-circle'></i>")
                $( "#{{ name }}-feedback" ).html(data)
            }, 2000)
            })

        } else {
            alert("Wrong input")
        }
    })
})
"""


class DeleteUnlinkedButton(Element):
    element_template = Template(DELETE_UNLINKED_HTML)
    js_template = Template(DELETE_UNLINKED_JS)

    def __init__(self, text: str = "Delete", **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def delete(self):
        query = {"exp_id": self.exp.exp_id, "type": self.exp.data_manager.UNLINKED_DATA}
        count = self.exp.db_unlinked.count_documents(query)
        result = self.exp.db_unlinked.delete_many(query)
        msg = (
            f"Deleted {result.deleted_count} of {count} documents in unlinked data"
            " collection."
        )
        self.exp.log.info(msg)
        return msg

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        self.url = self.exp.ui.add_callable(self.delete)

    def prepare_web_widget(self):
        self._js_code = []
        d = {}
        d["url"] = self.url
        d["name"] = self.name
        d["exptitle"] = self.exp.title
        js = self.js_template.render(d)
        self.add_js(js)

    @property
    def template_data(self):
        d = super().template_data
        d["exptitle"] = self.exp.title
        d["text"] = self.text
        d["name"] = self.name
        return d


@inherit_kwargs
class DeleteUnlinkedPage(ManagerPage):
    """
    Allows you to delete unlinked data for a specific experiment.

    Args:
        {kwargs}

    Examples:
        Minimal Example::

            import alfred3 as al
            from alfred3.admin import DeleteUnlinkedPage

            exp = al.Experiment()


            @exp.member(admin=True)
            class DeleteUnlinkedDemo(DeleteUnlinkedPage):
                pass


            @exp.member
            class TestUnlink(al.UnlinkedDataPage):
                def on_exp_access(self):
                    self += al.TextEntry(name="test")
    """

    title = "Delete Unlinked Data"

    def on_exp_access(self):
        self += VerticalSpace("150px")
        self += Text(
            "By clicking on this button, you can delete all unlinked data",
            align="center",
        )
        self += DeleteUnlinkedButton(font_size="14pt", align="center")
