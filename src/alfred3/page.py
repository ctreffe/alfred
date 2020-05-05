# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
'''
from __future__ import absolute_import

import time
from abc import ABCMeta, abstractproperty
from builtins import object, str
from functools import reduce

from future.utils import with_metaclass

from . import alfredlog, element, settings
from ._core import ContentCore
from ._helper import _DictObj
from .element import (Element, ExperimenterMessages, TextElement,
                      WebElementInterface)
from .exceptions import AlfredError

logger = alfredlog.getLogger(__name__)


class PageCore(ContentCore):
    def __init__(self, minimum_display_time=0, minimum_display_time_msg=None, values: dict = {}, run_on_showing='always', run_on_hiding='always', **kwargs):
        self._minimum_display_time = minimum_display_time
        if settings.debugmode and settings.debug.disable_minimum_display_time:
            self._minimum_display_time = 0
        self._minimum_display_time_msg = minimum_display_time_msg

        self._run_on_showing = run_on_showing
        self._run_on_hiding = run_on_hiding
        self._data = {}
        self._is_closed = False
        self._show_corrective_hints = False
        self._log = []  # insert tuple with ('type', msg) for logger

        super(PageCore, self).__init__(**kwargs)

        if not isinstance(values, dict):
            raise TypeError("The parameter 'values' requires a dictionary as input.")
        self.values = _DictObj(values)

        if self._run_on_showing not in ['once', 'always']:
            raise ValueError("The parameter 'run_on_showing' must be either 'once' or 'always'.")

    def added_to_experiment(self, experiment):
        if not isinstance(self, WebPageInterface):
            raise TypeError('%s must be an instance of %s' % (self.__class__.__name__, WebPageInterface.__name__))

        super(PageCore, self).added_to_experiment(experiment)

    def print_log(self):
        for i, _entry in enumerate(self._log):
            category, msg = self._log.pop(i)
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
        '''
        Method for internal processes on showing Widget
        '''

        if not self._has_been_shown:
            self._data['first_show_time'] = time.time()

        if self._run_on_showing == 'once' and not self._has_been_shown:
            self.on_showing_widget()
            self.on_showing()

        elif self._run_on_showing == 'always':
            self.on_showing_widget()
            self.on_showing()
            # self._log.append(('debug', 'The current page executes the "on_showing" method every time the page is shown. If you want to turn this behavior off, please use "run_on_showing=\'once\'" in the page initialisation.'))


        self._has_been_shown = True

    def on_showing_widget(self):
        pass

    def on_showing(self):
        pass

    def _on_hiding_widget(self):
        '''
        Method for internal processes on hiding Widget
        '''

        if self._run_on_hiding == 'once' and not self._has_been_hidden:
            self.on_hiding_widget()
            self.on_hiding()
        elif self._run_on_showing == 'always':
            self.on_hiding_widget()
            self.on_hiding()
            # self._log.append(('debug',
            #                  'The current page executes the "on_hiding" method every time the page is hidden. If you want to turn this behavior off, please use "run_on_hiding=\'once\'" in the page initialisation.'))

        self._has_been_hidden = True
        self.print_log()

        # TODO: Sollten nicht on_hiding closingtime und duration errechnet werden? Passiert momentan on_closing und funktioniert daher nicht in allen page groups!

    def on_hiding_widget(self):
        pass

    def on_hiding(self):
        pass

    def close_page(self):
        if not self.allow_closing:
            raise AlfredError()

        if 'closing_time' not in self._data:
            self._data['closing_time'] = time.time()
        if 'duration' not in self._data \
                and 'first_show_time' in self._data \
                and 'closing_time' in self._data:
            self._data['duration'] = self._data['closing_time'] - self._data['first_show_time']

        self._is_closed = True

    def allow_closing(self):
        return True

    def can_display_corrective_hints_in_line(self):
        return False

    def corrective_hints(self):
        '''
        returns a list of corrective hints

        :rtype: list of unicode strings
        '''
        return []

    def allow_leaving(self, direction):
        if 'first_show_time' in self._data and \
                time.time() - self._data['first_show_time'] \
                < self._minimum_display_time:
            try:
                msg = self._minimum_display_time_msg if self._minimum_display_time_msg else self._experiment.settings.messages.minimum_display_time
            except Exception:
                msg = "Can't access minimum display time message"
            self._experiment.message_manager.post_message(msg.replace('${mdt}', str(self._minimum_display_time)))
            return False
        return True


class WebPageInterface(with_metaclass(ABCMeta, object)):
    def prepare_web_widget(self):
        '''Wird aufgerufen bevor das die Frage angezeigt wird, wobei jedoch noch
        Nutzereingaben zwischen aufruf dieser funktion und dem anzeigen der
        Frage kmmen koennen. Hier sollte die Frage, von
        noch nicht gemachten user Eingaben unabhaengige und rechenintensive
        verbereitungen fuer das anzeigen des widgets aufrufen. z.B. generieren
        von grafiken'''
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
        self._log.append(('warning', "page.add_element() is deprecated. Use page.append() instead."))
        self.append(element)

    def add_elements(self, *elements):
        self._log.append(('warning', "page.add_elements() is deprecated. Use page.append() instead."))
        for elmnt in elements:
            self.append(elmnt)

    def append(self, *elements):
        for elmnt in elements:
            if not isinstance(elmnt, Element):
                raise TypeError

            exp_type = settings.experiment.type  # 'web' or 'qt-wk'

            if exp_type == 'web' and not isinstance(elmnt, WebElementInterface):
                raise TypeError("%s is not an instance of WebElementInterface" % type(elmnt).__name__)

            if isinstance(self, WebPageInterface) and not isinstance(elmnt, WebElementInterface):
                raise TypeError("%s is not an instance of WebElementInterface" % type(elmnt).__name__)

            if elmnt.name is None:
                elmnt.name = ("%02d" % self._element_name_counter) + '_' + elmnt.__class__.__name__
                self._element_name_counter = self._element_name_counter + 1

            self._element_list.append(elmnt)
            elmnt.added_to_page(self)

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
    def can_display_corrective_hints_in_line(self):
        return reduce(lambda b, element: b and element.can_display_corrective_hints_in_line, self._element_list, True)

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
        html = ''

        for elmnt in self._element_list:
            if elmnt.web_widget != '' and elmnt.should_be_shown:
                html = html + (
                            '<div class="row with-margin"><div id="elid-%s" class="element">' % elmnt.name) + elmnt.web_widget + '</div></div>'

        return html

    @property
    def web_thumbnail(self):
        '''
        gibt das thumbnail von self._thumbnail_element oder falls self._thumbnail_element nicht gesetzt, das erste thumbnail eines elements aus self._element_list zurueck.

        .. todo:: was ist im fall, wenn thumbnail element nicht gestzt ist? anders verhalten als jetzt???

        '''
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
        return ''

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
    def __init__(self, instruction=None, age=True, sex=True, course_of_studies=True, semester=True, **kwargs):
        super(DemographicPage, self).__init__(**kwargs)

        if instruction:
            self.append(element.TextElement(instruction))
        self.append(element.TextElement(u"Bitte gib deine persönlichen Datein ein."))
        if age:
            self.append(element.TextEntryElement(u"Dein Alter: ", name="age"))

        if sex:
            self.append(element.TextEntryElement(u"Dein Geschlecht: ", name="sex"))

        if course_of_studies:
            self.append(element.TextEntryElement(instruction=u"Dein Studiengang: ", name='course_of_studies'))

        if semester:
            self.append(element.TextEntryElement(instruction=u"Dein Fachsemester ", name='semester'))


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
        if 'first_show_time' not in self._data:
            exp_title = TextElement('Informationen zur Session:', font='big')

            exp_infos = '<table style="border-style: none"><tr><td width="200">Experimentname:</td><td>' + self._experiment.name + '</td></tr>'
            exp_infos = exp_infos + '<tr><td>Experimenttyp:</td><td>' + self._experiment.type + '</td></tr>'
            exp_infos = exp_infos + '<tr><td>Experimentversion:</td><td>' + self._experiment.version + '</td></tr>'
            exp_infos = exp_infos + '<tr><td>Experiment-ID:</td><td>' + self._experiment.exp_id + '</td></tr>'
            exp_infos = exp_infos + '<tr><td>Session-ID:</td><td>' + self._experiment.session_id + '</td></tr>'
            exp_infos = exp_infos + '<tr><td>Log-ID:</td><td>' + self._experiment.session_id[:6] + '</td></tr>'
            exp_infos = exp_infos + '</table>'

            exp_info_element = TextElement(exp_infos)

            self.append(exp_title, exp_info_element, ExperimenterMessages())

        super(ExperimentFinishPage, self).on_showing_widget()


class HeadOpenSectionCantClose(CompositePage):
    def __init__(self, **kwargs):
        super(HeadOpenSectionCantClose, self).__init__(**kwargs)

        self.append(element.TextElement(
            "Nicht alle Fragen konnten Geschlossen werden. Bitte korrigieren!!!<br /> Das hier wird noch besser implementiert"))


class MongoSaveCompositePage(CompositePage):
    def __init__(self, host, database, collection, user, password, error='ignore', hide_data=True, *args, **kwargs):
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
            data = {'tag': self.tag,
                    'uid': self.uid}
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
            data.pop('first_show_time', None)
            data.pop('closing_time', None)
            col.insert(data)
            self._saved = True
        except Exception as e:
            if self._error != 'ignore':
                raise e
        return rv


####################
# Page Mixins
####################

class WebTimeoutMixin(object):

    def __init__(self, timeout, **kwargs):
        super(WebTimeoutMixin, self).__init__(**kwargs)

        self._end_link = 'unset'
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
        code = (5, '''
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
        ''' % (self._timeout, self._end_link))
        js_code = super(WebTimeoutMixin, self).js_code
        if self._run_timeout:
            js_code.append(code)
        else:
            js_code.append((5, '''$(document).ready(function(){$(".timeout-label").html(0);});'''))
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
