# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""
from __future__ import absolute_import

import time
import logging
from abc import ABCMeta, abstractproperty, abstractmethod, ABC
from builtins import object, str
from functools import reduce

from future.utils import with_metaclass

from . import element, settings, alfredlog
from . import saving_agent
from ._core import ContentCore
from ._helper import _DictObj
from .element import Element, ExperimenterMessages, TextElement, WebElementInterface
from .exceptions import AlfredError


class PageCore(ContentCore):
    def __init__(
        self,
        minimum_display_time=0,
        minimum_display_time_msg=None,
        values: dict = {},
        run_on_showing="always",
        run_on_hiding="always",
        **kwargs,
    ):
        self._minimum_display_time = minimum_display_time
        if settings.debugmode and settings.debug.disable_minimum_display_time:
            self._minimum_display_time = 0
        self._minimum_display_time_msg = minimum_display_time_msg

        self._run_on_showing = run_on_showing
        self._run_on_hiding = run_on_hiding
        self._data = {}
        self._is_closed = False
        self._show_corrective_hints = False

        # e.g.: alfred3.page.Page
        self.log = alfredlog.QueuedLoggingInterface(base_logger=__name__)

        super(PageCore, self).__init__(**kwargs)

        if not isinstance(values, dict):
            raise TypeError("The parameter 'values' requires a dictionary as input.")
        self.values = _DictObj(values)

        if self._run_on_showing not in ["once", "always"]:
            raise ValueError("The parameter 'run_on_showing' must be either 'once' or 'always'.")

    def added_to_experiment(self, experiment):
        if not isinstance(self, WebPageInterface):
            raise TypeError(
                "%s must be an instance of %s"
                % (self.__class__.__name__, WebPageInterface.__name__)
            )

        super(PageCore, self).added_to_experiment(experiment)

        queue_logger_name = self.prepare_logger_name()
        self.log.queue_logger = logging.getLogger(queue_logger_name)
        self.log.session_id = self.experiment.config.get("metadata", "session_id")
        self.log.log_queued_messages()

    @property
    def show_thumbnail(self):
        return True

    @property
    def show_corrective_hints(self):
        return self._show_corrective_hints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        self._show_corrective_hints = bool(b)

    @property
    def is_closed(self):
        return self._is_closed

    @property
    def data(self):
        data = super(PageCore, self).data
        data.update(self._data)
        return data

    def _on_showing_widget(self):
        """
        Method for internal processes on showing Widget
        """

        if not self._has_been_shown:
            self._data["first_show_time"] = time.time()

        if self._run_on_showing == "once" and not self._has_been_shown:
            self.on_showing_widget()
            self.on_showing()

        elif self._run_on_showing == "always":
            self.on_showing_widget()
            self.on_showing()

        self._has_been_shown = True

    def on_showing_widget(self):
        pass

    def on_showing(self):
        pass

    def _on_hiding_widget(self):
        """
        Method for internal processes on hiding Widget
        """

        if self._run_on_hiding == "once" and not self._has_been_hidden:
            self.on_hiding_widget()
            self.on_hiding()
        elif self._run_on_showing == "always":
            self.on_hiding_widget()
            self.on_hiding()

        self._has_been_hidden = True

        # TODO: Sollten nicht on_hiding closingtime und duration errechnet werden? Passiert momentan on_closing und funktioniert daher nicht in allen page groups!

    def on_hiding_widget(self):
        pass

    def on_hiding(self):
        pass

    def close_page(self):
        if not self.allow_closing:
            raise AlfredError()

        if "closing_time" not in self._data:
            self._data["closing_time"] = time.time()
        if (
            "duration" not in self._data
            and "first_show_time" in self._data
            and "closing_time" in self._data
        ):
            self._data["duration"] = self._data["closing_time"] - self._data["first_show_time"]

        self._is_closed = True

    def allow_closing(self):
        return True

    def can_display_corrective_hints_in_line(self):
        return False

    def corrective_hints(self):
        """
        returns a list of corrective hints

        :rtype: list of unicode strings
        """
        return []

    def allow_leaving(self, direction):
        if (
            "first_show_time" in self._data
            and time.time() - self._data["first_show_time"] < self._minimum_display_time
        ):
            try:
                msg = (
                    self._minimum_display_time_msg
                    if self._minimum_display_time_msg
                    else self._experiment.settings.messages.minimum_display_time
                )
            except Exception:
                msg = "Can't access minimum display time message"
            self._experiment.message_manager.post_message(
                msg.replace("${mdt}", str(self._minimum_display_time))
            )
            return False
        return True

    def prepare_logger_name(self) -> str:
        """Returns a logger name for use in *self.log.queue_logger*.

        The name has the following format::

            exp.exp_id.module_name.class_name.class_uid
        
        with *class_uid* only added, if 
        :attr:`~PageCore.instance_level_logging` is set to *True*.
        """
        # remove "alfred3" from module name
        module_name = __name__.split(".")
        module_name.pop(0)

        name = []
        name.append("exp")
        name.append(self.experiment.exp_id)
        name.append(".".join(module_name))
        name.append(type(self).__name__)

        if self.instance_level_logging:
            name.append(self._uid)

        return ".".join(name)

    def save_data(self, level: int = 1, sync: bool = False):
        """Saves current experiment data.
        
        Collects the current experimental data and calls the 
        experiment's main SavingAgentController to save the data with
        all SavingAgents.

        Args: 
            level: Level of the saving task. High level means high 
                importance. If the level is below a SavingAgent's 
                activation level, that agent will not be used for 
                processing this task. Defaults to 1.
            sync: If True, the saving task will be prioritised and the
                experiment will pause until the task was fully completed.
                Should be used carefully. Defaults to False.
        """
        data = self._experiment.data_manager.get_data()
        self._experiment.sac_main.save_with_all_agents(data=data, level=level, sync=sync)


class WebPageInterface(with_metaclass(ABCMeta, object)):
    def prepare_web_widget(self):
        """Wird aufgerufen bevor das die Frage angezeigt wird, wobei jedoch noch
        Nutzereingaben zwischen aufruf dieser funktion und dem anzeigen der
        Frage kmmen koennen. Hier sollte die Frage, von
        noch nicht gemachten user Eingaben unabhaengige und rechenintensive
        verbereitungen fuer das anzeigen des widgets aufrufen. z.B. generieren
        von grafiken"""
        pass

    @abstractproperty
    def web_widget(self):
        pass

    @property
    def web_thumbnail(self):
        return None

    @property
    def css_code(self):
        return []

    @property
    def css_urls(self):
        return []

    @property
    def js_code(self):
        return []

    @property
    def js_urls(self):
        return []

    def set_data(self, dictionary):
        pass


class CoreCompositePage(PageCore):
    def __init__(self, elements=None, **kwargs):
        super(CoreCompositePage, self).__init__(**kwargs)

        self._element_list = []
        self._element_name_counter = 1
        self._thumbnail_element = None
        if elements is not None:
            if not isinstance(elements, list):
                raise TypeError
            for elmnt in elements:
                self.append(elmnt)

    def add_element(self, element):

        self.log.warning("page.add_element() is deprecated. Use page.append() instead.")

        self.append(element)

    def add_elements(self, *elements):
        self.log.warning("page.add_elements() is deprecated. Use page.append() instead.")

        for elmnt in elements:
            self.append(elmnt)

    def append(self, *elements):
        for elmnt in elements:
            if not isinstance(elmnt, Element):
                raise TypeError

            exp_type = settings.experiment.type  # 'web' or 'qt-wk'

            if exp_type == "web" and not isinstance(elmnt, WebElementInterface):
                raise TypeError(
                    "%s is not an instance of WebElementInterface" % type(elmnt).__name__
                )

            if isinstance(self, WebPageInterface) and not isinstance(elmnt, WebElementInterface):
                raise TypeError(
                    "%s is not an instance of WebElementInterface" % type(elmnt).__name__
                )

            if elmnt.name is None:
                elmnt.name = ("%02d" % self._element_name_counter) + "_" + elmnt.__class__.__name__
                self._element_name_counter = self._element_name_counter + 1

            self._element_list.append(elmnt)
            elmnt.added_to_page(self)

    def added_to_experiment(self, experiment):
        super().added_to_experiment(experiment)
        for element in self._element_list:
            element.activate(experiment)

    @property
    def allow_closing(self):
        return reduce(lambda b, element: element.validate_data() and b, self._element_list, True)

    def close_page(self):
        super(CoreCompositePage, self).close_page()

        for elmnt in self._element_list:
            elmnt.enabled = False

    @property
    def data(self):
        data = super(CoreCompositePage, self).data
        for elmnt in self._element_list:
            data.update(elmnt.data)

        return data

    @property
    def codebook_data(self):
        data = {}
        for el in self._element_list:
            key = self.tree.replace("rootSection.", "") + "." + el.name
            try:
                data.update(el.codebook_data)
            except AttributeError:
                pass
        return data

    @property
    def can_display_corrective_hints_in_line(self):
        return reduce(
            lambda b, element: b and element.can_display_corrective_hints_in_line,
            self._element_list,
            True,
        )

    @property
    def show_corrective_hints(self):
        return self._show_corrective_hints

    @show_corrective_hints.setter
    def show_corrective_hints(self, b):
        b = bool(b)
        self._show_corrective_hints = b
        for elmnt in self._element_list:
            elmnt.show_corrective_hints = b

    @property
    def corrective_hints(self):
        # only display hints if property is True
        if not self.show_corrective_hints:
            return []

        # get corrective hints for each element
        list_of_lists = []

        for elmnt in self._element_list:
            if not elmnt.can_display_corrective_hints_in_line and elmnt.corrective_hints:
                list_of_lists.append(elmnt.corrective_hints)

        # flatten list
        return [item for sublist in list_of_lists for item in sublist]

    def set_data(self, dictionary):
        for elmnt in self._element_list:
            elmnt.set_data(dictionary)


class WebCompositePage(CoreCompositePage, WebPageInterface):
    def prepare_web_widget(self):
        for elmnt in self._element_list:
            elmnt.prepare_web_widget()

    @property
    def web_widget(self):
        html = ""

        for elmnt in self._element_list:
            if elmnt.web_widget != "" and elmnt.should_be_shown:
                html = (
                    html
                    + (
                        '<div class="row with-margin"><div id="elid-%s" class="element">'
                        % elmnt.name
                    )
                    + elmnt.web_widget
                    + "</div></div>"
                )

        return html

    @property
    def web_thumbnail(self):
        """
        gibt das thumbnail von self._thumbnail_element oder falls self._thumbnail_element nicht gesetzt, das erste thumbnail eines elements aus self._element_list zurueck.

        .. todo:: was ist im fall, wenn thumbnail element nicht gestzt ist? anders verhalten als jetzt???

        """
        if not self.show_thumbnail:
            return None

        if self._thumbnail_element:
            return self._thumbnail_element.web_thumbnail
        else:
            for elmnt in self._element_list:
                if elmnt.web_thumbnail and elmnt.should_be_shown:
                    return elmnt.web_thumbnail
            return None

    @property
    def css_code(self):
        return reduce(lambda l, element: l + element.css_code, self._element_list, [])

    @property
    def css_urls(self):
        return reduce(lambda l, element: l + element.css_urls, self._element_list, [])

    @property
    def js_code(self):
        return reduce(lambda l, element: l + element.js_code, self._element_list, [])

    @property
    def js_urls(self):
        return reduce(lambda l, element: l + element.js_urls, self._element_list, [])


class CompositePage(WebCompositePage):
    pass


class Page(WebCompositePage):
    pass


class PagePlaceholder(PageCore, WebPageInterface):
    def __init__(self, ext_data={}, **kwargs):
        super(PagePlaceholder, self).__init__(**kwargs)

        self._ext_data = ext_data

    @property
    def web_widget(self):
        return ""

    @property
    def data(self):
        data = super(PageCore, self).data
        data.update(self._ext_data)
        return data

    @property
    def should_be_shown(self):
        return False

    @should_be_shown.setter
    def should_be_shown(self, b):
        pass

    @property
    def is_jumpable(self):
        return False

    @is_jumpable.setter
    def is_jumpable(self, is_jumpable):
        pass


class DemographicPage(CompositePage):
    def __init__(
        self, instruction=None, age=True, sex=True, course_of_studies=True, semester=True, **kwargs
    ):
        super(DemographicPage, self).__init__(**kwargs)

        if instruction:
            self.append(element.TextElement(instruction))
        self.append(element.TextElement("Bitte gib deine persönlichen Datein ein."))
        if age:
            self.append(element.TextEntryElement("Dein Alter: ", name="age"))

        if sex:
            self.append(element.TextEntryElement("Dein Geschlecht: ", name="sex"))

        if course_of_studies:
            self.append(
                element.TextEntryElement(
                    instruction="Dein Studiengang: ", name="course_of_studies"
                )
            )

        if semester:
            self.append(
                element.TextEntryElement(instruction="Dein Fachsemester ", name="semester")
            )


class AutoHidePage(CompositePage):
    def __init__(self, on_hiding=False, on_closing=True, **kwargs):
        super(AutoHidePage, self).__init__(**kwargs)

        self._on_closing = on_closing
        self._on_hiding = on_hiding

    def on_hiding_widget(self):
        if self._on_hiding:
            self.should_be_shown = False

    def close_page(self):
        super(AutoHidePage, self).close_page()
        if self._on_closing:
            self.should_be_shown = False


class ExperimentFinishPage(CompositePage):
    def on_showing_widget(self):
        if "first_show_time" not in self._data:
            exp_title = TextElement("Informationen zur Session:", font="big")

            exp_infos = (
                '<table style="border-style: none"><tr><td width="200">Experimentname:</td><td>'
                + self._experiment.name
                + "</td></tr>"
            )
            exp_infos = (
                exp_infos
                + "<tr><td>Experimenttyp:</td><td>"
                + self._experiment.type
                + "</td></tr>"
            )
            exp_infos = (
                exp_infos
                + "<tr><td>Experimentversion:</td><td>"
                + self._experiment.version
                + "</td></tr>"
            )
            exp_infos = (
                exp_infos
                + "<tr><td>Experiment-ID:</td><td>"
                + self._experiment.exp_id
                + "</td></tr>"
            )
            exp_infos = (
                exp_infos
                + "<tr><td>Session-ID:</td><td>"
                + self._experiment.session_id
                + "</td></tr>"
            )
            exp_infos = (
                exp_infos
                + "<tr><td>Log-ID:</td><td>"
                + self._experiment.session_id[:6]
                + "</td></tr>"
            )
            exp_infos = exp_infos + "</table>"

            exp_info_element = TextElement(exp_infos)

            self.append(exp_title, exp_info_element, ExperimenterMessages())

        super(ExperimentFinishPage, self).on_showing_widget()


class HeadOpenSectionCantClose(CompositePage):
    def __init__(self, **kwargs):
        super(HeadOpenSectionCantClose, self).__init__(**kwargs)

        self.append(
            element.TextElement(
                "Nicht alle Fragen konnten Geschlossen werden. Bitte korrigieren!!!<br /> Das hier wird noch besser implementiert"
            )
        )


class MongoSaveCompositePage(CompositePage):
    def __init__(
        self,
        host,
        database,
        collection,
        user,
        password,
        error="ignore",
        hide_data=True,
        *args,
        **kwargs,
    ):
        super(MongoSaveCompositePage, self).__init__(*args, **kwargs)
        self._host = host
        self._database = database
        self._collection = collection
        self._user = user
        self._password = password
        self._error = error
        self._hide_data = hide_data
        self._saved = False

    @property
    def data(self):
        if self._hide_data:
            # this is needed for some other functions to work properly
            data = {"tag": self.tag, "uid": self.uid}
            return data
        else:
            return super(MongoSaveCompositePage, self).data

    def close_page(self):
        rv = super(MongoSaveCompositePage, self).close_page()
        if self._saved:
            return rv
        from pymongo import MongoClient

        try:
            client = MongoClient(self._host)
            db = client[self._database]
            db.authenticate(self._user, self._password)
            col = db[self._collection]
            data = super(MongoSaveCompositePage, self).data
            data.pop("first_show_time", None)
            data.pop("closing_time", None)
            col.insert(data)
            self._saved = True
        except Exception as e:
            if self._error != "ignore":
                raise e
        return rv


####################
# Page Mixins
####################


class WebTimeoutMixin(object):
    def __init__(self, timeout, **kwargs):
        super(WebTimeoutMixin, self).__init__(**kwargs)

        self._end_link = "unset"
        self._run_timeout = True
        self._timeout = timeout
        if settings.debugmode and settings.debug.reduce_countdown:
            self._timeout = int(settings.debug.reduced_countdown_time)

    def added_to_experiment(self, experiment):
        super(WebTimeoutMixin, self).added_to_experiment(experiment)
        self._end_link = self._experiment.user_interface_controller.add_callable(self.callback)

    def callback(self, *args, **kwargs):
        self._run_timeout = False
        self._experiment.user_interface_controller.update_with_user_input(kwargs)
        return self.on_timeout(*args, **kwargs)

    def on_hiding_widget(self):
        self._run_timeout = False
        super(WebTimeoutMixin, self).on_hiding_widget()

    def on_timeout(self, *args, **kwargs):
        pass

    @property
    def js_code(self):
        code = (
            5,
            """
            $(document).ready(function(){
                var start_time = new Date();
                var timeout = %s;
                var action_url = '%s';

                var update_counter = function() {
                    var now = new Date();
                    var time_left = timeout - Math.floor((now - start_time) / 1000);
                    if (time_left < 0) {
                        time_left = 0;
                    }
                    $(".timeout-label").html(time_left);
                    if (time_left > 0) {
                        setTimeout(update_counter, 200);
                    }
                };
                update_counter();

                var timeout_function = function() {
                    $("#form").attr("action", action_url);
                    $("#form").submit();
                };
                setTimeout(timeout_function, timeout*1000);
            });
        """
            % (self._timeout, self._end_link),
        )
        js_code = super(WebTimeoutMixin, self).js_code
        if self._run_timeout:
            js_code.append(code)
        else:
            js_code.append((5, """$(document).ready(function(){$(".timeout-label").html(0);});"""))
        return js_code


class WebTimeoutForwardMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self._experiment.user_interface_controller.move_forward()


class WebTimeoutCloseMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self.close_page()


class HideButtonsMixin(object):
    def _on_showing_widget(self):
        self._experiment.user_interface_controller.layout.forward_enabled = False
        self._experiment.user_interface_controller.layout.backward_enabled = False
        self._experiment.user_interface_controller.layout.jump_list_enabled = False
        self._experiment.user_interface_controller.layout.finish_disabled = True

        super(HideButtonsMixin, self)._on_showing_widget()

    def _on_hiding_widget(self):
        self._experiment.user_interface_controller.layout.forward_enabled = True
        self._experiment.user_interface_controller.layout.backward_enabled = True
        self._experiment.user_interface_controller.layout.jump_list_enabled = True
        self._experiment.user_interface_controller.layout.finish_disabled = False

        super(HideButtonsMixin, self)._on_hiding_widget()


####################
# Pages with Mixins
####################


class WebTimeoutForwardPage(WebTimeoutForwardMixin, WebCompositePage):
    pass


class WebTimeoutClosePage(WebTimeoutCloseMixin, WebCompositePage):
    pass


class NoDataPage(Page):
    """This Page does not save any data except its tag and uid."""

    @property
    def data(self):
        # Pages must always return tag and uid!
        data = {"tag": self.tag, "uid": self.uid}

        return data


class UnlinkedDataPage(NoDataPage):
    """This Page saves unlinked data.

    Unlinked data is data that does not contain any identifiers that
    would allow someone to establish a connection between an 
    experiment data set and the unlinked data set. 
    A common use case is the sepration of identifying personal 
    information that might be needed for non-experimental purposes such 
    as compensation admninistration, from experiment data.

    In practice that means that the UnlinkedDataPage does not save any
    of the following:

    - Time of saving
    - Session ID
    - Experiment condition
    - Additional data
    - Start time
    - Experiment version
    - Alfred version

    It will, however, save the following information:

    - Experiment Title
    - Experiment ID
    - Experiment Author
    - Page tag
    - Page ID

    Thus, the saved data *can* be linked to an *experiment* and to a
    page. That is intended and indeed necessary so that data 
    can be retrieved and processed. The key point is that there is no
    identifier for linking data to data from a specific experimental 
    *session* (i.e. the name of a subject, saved with an 
    UnlinkedDataPage cannot be linked to his/her answers given on other
    Pages).

    .. warning::
        All data from UnlinkedDataPages is saved in a single unlinked 
        document.

    """

    @property
    def unlinked_data(self):
        data = super(PageCore, self).data
        for elmnt in self._element_list:
            data.update(elmnt.data)
        return data

    def save_data(self, level: int = 1, sync: bool = False):
        """Saves current unlinked data.
        
        Collects the unlinked data from all UnlinkedDataPages in the
        experiment and engages the experiment's unlinked
        SavingAgentController to save the data with all SavingAgents.

        Args: 
            level: Level of the saving task. High level means high 
                importance. If the level is below a SavingAgent's 
                activation level, that agent will not be used for 
                processing this task. Defaults to 1.
            sync: If True, the saving task will be prioritised and the
                experiment will pause until the task was fully completed.
                Should be used carefully. Defaults to False.
        """
        data = self._experiment.data_manager.get_unlinked_data()
        self._experiment.sac_unlinked.save_with_all_agents(data=data, level=level, sync=sync)


class CustomSavingPage(Page, ABC):
    """Allows you to add custom SavingAgents directly to the page.

    Since this is an abstract class, it can not be instantiated directly.
    You have to derive a child class and define the property
    :meth:`custom_save_data`, which must return a dictionary. Through
    this property, you control exactly which data will be saved by this
    page.

    Example 1: Saving ordinary page data (like other pages)::

        class MyPage(CustomSavingPage):

            @property
            def custom_save_data(self):
                return self.data


    Example 2: Saving a static dictionary

        class MyPage(CustomSavingPage):

            @property
            def custom_save_data(self):
                return {"key": "value"}

    .. warning::
        Each SavingAgent maintains one file or one document. 
        On saving, the document will be fully replaced with the current
        data. That means, you should never let two CustomSavingPages
        share a SavingAgent, as they will override each other's data.

    Args:
        experiment: Alfred experiment. This page must be initialized
            with an experiment.
        save_to_main: If True, data will be *also* saved using the
            experiment's main SavingAgentController and all of its
            SavingAgents. Defaults to False.
    """

    def __init__(self, experiment, save_to_main: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._experiment = experiment
        self.saving_agent_controller = saving_agent.SavingAgentController(self._experiment)
        self.save_to_main = save_to_main

    def added_to_experiment(self, experiment):
        if not self._experiment:
            super().added_to_experiment(experiment=experiment)
            self.saving_agent_controller = saving_agent.SavingAgentController(self._experiment)
        self._check_for_duplicate_agents()

    def _check_for_duplicate_agents(self):
        comparison = []
        comparison += list(self._experiment.sac_main.agents.values())
        comparison += list(self._experiment.sac_unlinked.agents.values())

        for pg in self._experiment.page_controller.pages():
            if pg == self:
                continue
            try:
                comparison += list(pg.saving_agent_controller.agents.values())
            except AttributeError:
                pass

        for agent in self.saving_agent_controller.agents.values():
            self._check_one_duplicate(agent, comparison)

    @staticmethod
    def _check_one_duplicate(agent, agents_list):
        for ag in agents_list:
            if ag == agent:
                raise ValueError("A SavingAgent added to a CustomSavingPage must be unique")

    def append_saving_agents(self, *args):
        for agent in args:
            self.saving_agent_controller.append(agent)
        self._check_for_duplicate_agents()

    def append_failure_saving_agents(self, *args):
        for agent in args:
            self.saving_agent_controller.append_failure_agent(agent)

    @abstractproperty
    def custom_save_data(self):
        pass

    def save_data(self, level=1, sync=False):

        if not isinstance(self.custom_save_data, dict):
            raise ValueError("The porperty 'custom_page_data' must return a dictionary.")

        if self.save_to_main:
            self._experiment.sac_main.save_with_all_agents(level=level, sync=sync)

        self.saving_agent_controller.save_with_all_agents(
            data=self.custom_save_data, level=level, sync=sync
        )

