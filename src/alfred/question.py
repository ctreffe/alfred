# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
'''

from abc import ABCMeta, abstractmethod, abstractproperty
import time
import os.path

from _core import QuestionCore, package_path, Direction
from element import Element, WebElementInterface, QtElementInterface, TextElement, ExperimenterMessages
from exceptions import AlfredError
import element
from helpmates.concurrent import AsyncTask
import alfred.settings as settings

from PySide.QtGui import QWidget, QVBoxLayout, QShortcut, QSizePolicy, QScrollArea, QLayout
from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile, Slot, Qt


class Question(QuestionCore):
    def __init__(self, minimumDisplayTime=0, minimumDisplayTimeMsg=None,**kwargs):
        self._minimumDisplayTime = minimumDisplayTime
        if settings.debugmode and settings.debug.disableMinimumDisplayTime:
            self._minimumDisplayTime = 0
        self._minimumDisplayTimeMsg = minimumDisplayTimeMsg

        self._data = {}
        self._isClosed = False
        self._showCorrectiveHints = False

        super(Question, self).__init__(**kwargs)

    def addedToExperiment(self, experiment):
        if experiment.type == 'web' and not isinstance(self, WebQuestionInterface):
            raise TypeError('%s must be an instance of %s' % (self.__class__.__name__, WebQuestionInterface.__name__))

        if experiment.type == 'qt' and not isinstance(self, QtQuestionInterface):
            raise TypeError('%s must be an instance of %s' % (self.__class__.__name__, QtQuestionInterface.__name__))

        super(Question, self).addedToExperiment(experiment)

    @property
    def showThumbnail(self):
        return True

    @property
    def showCorrectiveHints(self):
        return self._showCorrectiveHints

    @showCorrectiveHints.setter
    def showCorrectiveHints(self, b):
        self._showCorrectiveHints = bool(b)


    @property
    def isClosed(self):
        return self._isClosed

    @property
    def data(self):
        data = super(Question, self).data
        data.update(self._data)
        return data


    def _onShowingWidget(self):
        '''
        Method for internal processes on showing Widget
        '''

        if not self._hasBeenShown:
            self._data['firstShowTime'] = time.time()

        self.onShowingWidget()

        self._hasBeenShown = True

    def onShowingWidget(self):
        pass

    def _onHidingWidget(self):
        '''
        Method for internal processes on hiding Widget
        '''
        self.onHidingWidget()

        self._hasBeenHidden = True

        #TODO: Sollten nicht onHiding closingtime und duration errechnet werden? Passiert momentan onClosing und funktioniert daher nicht in allen question groups!

    def onHidingWidget(self):
        pass

    def closeQuestion(self):
        if not self.allowClosing:
            raise AlfredError()

        if not self._data.has_key('closingTime'):
            self._data['closingTime'] = time.time()
        if not self._data.has_key('duration') \
             and self._data.has_key('firstShowTime') \
             and self._data.has_key('closingTime'):
                 self._data['duration'] = self._data['closingTime'] - self._data['firstShowTime']

        self._isClosed = True

    def allowClosing(self):
        return True

    def canDisplayCorrectiveHintsInline(self):
        return False

    def correctiveHints(self):
        '''
        returns a list of corrective hints

        :rtype: list of unicode strings
        '''
        return []



    def allowLeaving(self, direction):
        if self._data.has_key('firstShowTime') and \
                time.time() - self._data['firstShowTime'] \
                        < self._minimumDisplayTime:
            try:
                msg = self._minimumDisplayTimeMsg if self._minimumDisplayTimeMsg else self._experiment.settings.messages.minimum_display_time
            except:
                msg = "Can't access minimum display time message"
            self._experiment.messageManager.postMessage(msg.replace('${mdt}', str(self._minimumDisplayTime)))
            return False
        return True


class QtQuestionInterface(object):
    __metaclass__ = ABCMeta

    def prepareQtWidget(self):
        '''Wird aufgerufen bevor das die Frage angezeigt wird, wobei jedoch noch
        Nutzereingaben zwischen aufruf dieser funktion und dem anzeigen der
        Frage kmmen koennen. Hier sollte die Frage, von
        noch nicht gemachten user Eingaben unabhaengige und rechenintensive
        verbereitungen fuer das anzeigen des widgets aufrufen. z.B. generieren
        von grafiken'''
        pass

    @abstractproperty
    def qtWidget(self):
        pass

    @property
    def qtThumbnail(self):
        return None

class WebQuestionInterface(object):
    __metaclass__ = ABCMeta

    def prepareWebWidget(self):
        '''Wird aufgerufen bevor das die Frage angezeigt wird, wobei jedoch noch
        Nutzereingaben zwischen aufruf dieser funktion und dem anzeigen der
        Frage kmmen koennen. Hier sollte die Frage, von
        noch nicht gemachten user Eingaben unabhaengige und rechenintensive
        verbereitungen fuer das anzeigen des widgets aufrufen. z.B. generieren
        von grafiken'''
        pass

    @abstractproperty
    def webWidget(self):
        pass

    @property
    def webThumbnail(self):
        return None

    @property
    def cssCode(self):
        return []

    @property
    def cssURLs(self):
        return []

    @property
    def jsCode(self):
        return  []

    @property
    def jsURLs(self):
        return []

    def setData(self, dictionary):
        pass


class CoreCompositeQuestion(Question):
    def __init__(self, elements = None, **kwargs):
        super(CoreCompositeQuestion, self).__init__(**kwargs)

        self._elementList = []
        self._elementNameCounter = 1
        self._thumbnail_element = None
        if elements is not None:
            if not isinstance(elements, list):
                raise TypeError
            for element in elements:
                self.addElement(element)

    def addElement(self, element):
        if not isinstance(element, Element):
            raise TypeError

        expType = settings.experiment.type # 'web', 'qt' or 'qt-wk'

        if expType == 'web' and not isinstance(element, WebElementInterface):
            raise TypeError("%s is not an instance of WebElementInterface" % type(element).__name__)

        if expType == 'qt' and not isinstance(element, QtElementInterface):
            raise TypeError("%s is not an instance of QtElementInterface" % type(element).__name__)

        if isinstance(self, WebQuestionInterface) and not isinstance(self, QtQuestionInterface):
            if not isinstance(element, WebElementInterface):
                raise TypeError("%s is not an instance of WebElementInterface" % type(element).__name__)

        if isinstance(self, QtQuestionInterface) and not isinstance(self, WebQuestionInterface):
            if not isinstance(element, QtElementInterface):
                raise TypeError("%s is not an instance of QtElementInterface" % type(element).__name__)

        if element.name is None:
            element.name = ("%02d" % self._elementNameCounter) + '_' + element.__class__.__name__
            self._elementNameCounter = self._elementNameCounter + 1

        self._elementList.append(element)
        element.addedToQuestion(self)

    def addElements(self, *elements):
        for element in elements:
            self.addElement(element)

    @property
    def allowClosing(self):
        return reduce(lambda b, element: element.validateData() and b, self._elementList, True)

    def closeQuestion(self):
        super(CoreCompositeQuestion, self).closeQuestion()

        for element in self._elementList:
            element.enabled = False

    @property
    def data(self):
        data = super(CoreCompositeQuestion, self).data
        for element in self._elementList:
            data.update(element.data)

        return data

    @property
    def canDisplayCorrectiveHintsInline(self):
        return reduce(lambda b, element: b and element.canDisplayCorrectiveHintsInline, self._elementList, True)

    @property
    def showCorrectiveHints(self):
        return self._showCorrectiveHints

    @showCorrectiveHints.setter
    def showCorrectiveHints(self, b):
        b = bool(b)
        self._showCorrectiveHints = b
        for element in self._elementList:
            element.showCorrectiveHints = b

    @property
    def correctiveHints(self):
        # only display hints if property is True
        if not self.showCorrectiveHints:
            return []

        # get corrective hints for each element
        list_of_lists = []


        for element in self._elementList:
            if not element.canDisplayCorrectiveHintsInline and element.correctiveHints:
                list_of_lists.append(element.correctiveHints)

        # flatten list
        return [item for sublist in list_of_lists for item in sublist]

    def setData(self, dictionary):
        for element in self._elementList:
            element.setData(dictionary)

class WebCompositeQuestion(CoreCompositeQuestion, WebQuestionInterface):
    def prepareWebWidget(self):
        for element in self._elementList:
            element.prepareWebWidget()

    @property
    def webWidget(self):
        html = ''

        for element in self._elementList:
            if element.webWidget != '' and element.shouldBeShown:
                html = html + ('<div class="row with-margin"><div id="elid-%s" class="element">' % element.name) + element.webWidget + '</div></div>'

        return html

    @property
    def webThumbnail(self):
        '''
        gibt das thumbnail von self._thumbnail_element oder falls self._thumbnail_element nicht gesetzt, das erste thumbnail eines elements aus self._elementList zurueck.

        gleiches gilt für qtThumbnail

        .. todo:: was ist im fall, wenn thumbnail element nicht gestzt ist? anders verhalten als jetzt???

        '''
        if not self.showThumbnail:
            return None

        if self._thumbnail_element:
            return self._thumbnail_element.webThumbnail
        else:
            for element in self._elementList:
                if element.webThumbnail and element.shouldBeShown:
                    return element.webThumbnail
            return None

    @property
    def cssCode(self):
        return reduce(lambda l, element: l + element.cssCode, self._elementList, [])

    @property
    def cssURLs(self):
        return reduce(lambda l, element: l + element.cssURLs, self._elementList, [])

    @property
    def jsCode(self):
        return reduce(lambda l, element: l + element.jsCode, self._elementList, [])

    @property
    def jsURLs(self):
        return reduce(lambda l, element: l + element.jsURLs, self._elementList, [])


class QtCompositeQuestion(CoreCompositeQuestion, QtQuestionInterface):
    '''
    hier muss das QuestionInterface (abstrakt) implementiert werden, mit prepare widget können rechenintensive aufgaben erledigt werden, z.b. daten laden...
    beim widget müssen die elements zusammengesetzt werden (for-Schleife wie früher)

    '''
    def __init__(self, elements = None, **kwargs):
        super(QtCompositeQuestion, self).__init__(elements, **kwargs)
        self._questionWidget = None

    def prepareQtWidget(self):

        for element in self._elementList:
            element.maximumWidgetWidth = self._experiment.userInterfaceController.layout.maximumWidgetWidth
            element.prepareQtWidget()

    @property
    def qtWidget(self):
        '''
        '''
        if self._questionWidget == None:

            self._questionWidget = QWidget()

            self._contentLayout = QVBoxLayout()
            self._contentLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
            self._contentLayout.setSpacing(30)

            self._questionWidget.setLayout(self._contentLayout)

        widgetSet = True

        #Hier das Layout leeren!
        while widgetSet:
            widget = self._contentLayout.takeAt(0)
            if widget == None:
                widgetSet = False
            elif isinstance(widget, QWidget):
                widget.widget().setParent(None)
                widget.hide()

        for element in self._elementList:
            if element.shouldBeShown:
                elementWidget = element.qtWidget

                elementLayout = QVBoxLayout()
                elementLayout.addWidget(elementWidget)

                elementLayout.setAlignment(Qt.AlignLeft)

                if element.alignment == 'center':
                    elementLayout.setAlignment(Qt.AlignHCenter)

                if element.alignment == 'right':
                    elementLayout.setAlignment(Qt.AlignRight)

                self._contentLayout.addLayout(elementLayout)

        self._contentLayout.addStretch()

        return self._questionWidget


    @property
    def qtThumbnail(self):
        if self._thumbnail_element:
            return self._thumbnail_element.qtThumbnail
        else:
            for element in self._elementList:
                if element.qtThumbnail and element.shouldBeShown:
                    return element.qtThumbnail
            return None


class CompositeQuestion(QtCompositeQuestion, WebCompositeQuestion):
    pass

class QuestionPlaceholder(Question, WebQuestionInterface):
    def __init__(self, extData={}, **kwargs):
        super(QuestionPlaceholder, self).__init__(**kwargs)

        self._extData = extData


    @property
    def webWidget(self):
        return ''

    @property
    def data(self):
        data = super(Question, self).data
        data.update(self._extData)
        return data

    @property
    def shouldBeShown(self):
        return False

    @shouldBeShown.setter
    def shouldBeShown(self, b):
        pass

    @property
    def isJumpable(self):
        return False

    @isJumpable.setter
    def isJumpable(self, isJumpable):
        pass



class DemographicQuestion(CompositeQuestion):
    def __init__(self,  instruction=None, age=True, sex=True, courseOfStudies=True, semester=True, **kwargs):
        super(DemographicQuestion, self).__init__(**kwargs)


        if instruction:
            self.addElement(element.TextElement(instruction))
        self.addElement(element.TextElement(u"Bitte gib deine persönlichen Datein ein."))
        if age:
            self.addElement(element.TextEntryElement(u"Dein Alter: ", name="age"))

        if sex:
            self.addElement(element.TextEntryElement(u"Dein Geschlecht: ", name="sex"))

        if courseOfStudies:
            self.addElement(element.TextEntryElement(instruction=u"Dein Studiengang: ", name = 'courseOfStudies'))

        if semester:
            self.addElement(element.TextEntryElement(instruction=u"Dein Fachsemester ", name = 'semester'))


class AutoHideQuestion(CompositeQuestion):
    def __init__(self, onHiding=False, onClosing=True, **kwargs):
        super(AutoHideQuestion, self).__init__(**kwargs)

        self._onClosing = onClosing
        self._onHiding = onHiding

    def onHidingWidget(self):
        if self._onHiding:
            self.shouldBeShown = False

    def closeQuestion(self):
        super(AutoHideQuestion, self).closeQuestion()
        if self._onClosing:
            self.shouldBeShown = False


class QtCountdownQuestion(QtCompositeQuestion):
    class Countdown(AsyncTask):
        def doInBackground(self,params):
            delay, parent = params
            time.sleep(delay)
            return parent

        def onPostExecute(self, parent):
            parent.endOfCountDown()

    def __init__(self, t=5, **kwargs):
        super(QtCountdownQuestion, self).__init__(**kwargs)

        self._started = False
        self._t = t

        if settings.debugmode and settings.debug.reduceCountdown:
            self._t = int(settings.debug.reducedCountdownTime)

    def onShowingWidget(self):
        super(QtCountdownQuestion, self).onShowingWidget()
        self._counter = self.Countdown()
        self._counter.execute((self._t,self))

    def onHidingWidget(self):
        super(QtCountdownQuestion, self).onHidingWidget()
        self._counter.cancel()

    def endOfCountDown(self):
        if not self._counter.isCancelled():
            self._experiment.userInterfaceController.moveForward()


class QtKeyInputQuestion(QtCompositeQuestion):
    __metaclass__ = ABCMeta

    def __init__(self,keySequence = 'a', **kwargs):
        super(QtKeyInputQuestion, self).__init__(**kwargs)
        self._keySequence = keySequence

    @property
    def qtWidget(self):
        '''
        '''
        self._questionWidget = super(QtKeyInputQuestion, self).qtWidget

        self._shortCut = QShortcut(self._keySequence, self._questionWidget)
        self._shortCut.activated.connect(self.shortCutActivated)

        self._questionWidget.grabKeyboard()

        return self._questionWidget

    @abstractmethod
    @Slot()
    def shortCutActivated(self):
        pass


class ExperimentFinishQuestion(CompositeQuestion):
    def onShowingWidget(self):
        if not self._data.has_key('firstShowTime'):
            exp_title = TextElement('Informationen zur Session:', font = 'big')

            exp_infos = '<table style="border-style: none"><tr><td width="200">Experimentname:</td><td>'+self._experiment.name+'</td></tr>'
            exp_infos = exp_infos + '<tr><td>Experimenttyp:</td><td>'+self._experiment.type+'</td></tr>'
            exp_infos = exp_infos + '<tr><td>Experimentversion:</td><td>'+self._experiment.version+'</td></tr>'
            exp_infos = exp_infos + '<tr><td>Session-ID:</td><td>'+self._experiment.uuid+'</td></tr>'
            exp_infos = exp_infos + '<tr><td>Log-ID:</td><td>'+self._experiment.uuid[:6]+'</td></tr>'
            exp_infos = exp_infos + '</table>'

            exp_info_element = TextElement(exp_infos)

            self.addElements(exp_title, exp_info_element, ExperimenterMessages())

        super(ExperimentFinishQuestion, self).onShowingWidget()


class HeadOpenQGCantClose(CompositeQuestion):
    def __init__(self, **kwargs):
        super(HeadOpenQGCantClose, self).__init__(**kwargs)

        self.addElement(element.TextElement("Nicht alle Fragen konnten Geschlossen werden. Bitte korrigieren!!!<br /> Das hier wird noch besser implementiert"))


class MongoSaveCompositeQuestion(CompositeQuestion):
    def __init__(self, host, database, collection, user, password, error='ignore', hideData=True, *args, **kwargs):
        super(MongoSaveCompositeQuestion, self).__init__(*args, **kwargs)
        self._host = host
        self._database = database
        self._collection = collection
        self._user = user
        self._password = password
        self._error = error
        self._hide_data = hideData
        self._saved = False

    @property
    def data(self):
        if self._hide_data:
            # this is needed for some other functions to work properly
            data = {'tag' : self.tag,
                    'uid' : self.uid}
            return data
        else:
            return super(MongoSaveCompositeQuestion, self).data

    def closeQuestion(self):
        rv = super(MongoSaveCompositeQuestion, self).closeQuestion()
        if self._saved:
            return rv
        from pymongo import MongoClient
        try:
            client = MongoClient(self._host)
            db = client[self._database]
            db.authenticate(self._user, self._password)
            col = db[self._collection]
            data = super(MongoSaveCompositeQuestion, self).data
            data.pop('firstShowTime', None)
            data.pop('closingTime', None)
            col.insert(data)
            self._saved = True
        except Exception as e:
            if self._error != 'ignore':
                raise e
        return rv



####################
# Question Mixins
####################

class WebTimeoutMixin(object):

    def __init__(self, timeout, **kwargs):
        super(WebTimeoutMixin, self).__init__(**kwargs)

        self._end_link = 'unset'
        self._run_timeout = True
        self._timeout = timeout
        if settings.debugmode and settings.debug.reduceCountdown:
            self._timeout = int(settings.debug.reducedCountdownTime)

    def addedToExperiment(self, experiment):
        super(WebTimeoutMixin, self).addedToExperiment(experiment)
        self._end_link = self._experiment.userInterfaceController.addCallable(self.callback)

    def callback(self, *args, **kwargs):
        self._run_timeout = False
        self._experiment.userInterfaceController.updateWithUserInput(kwargs)
        return self.on_timeout(*args, **kwargs)

    def onHidingWidget(self):
        self._run_timeout = False
        super(WebTimeoutMixin, self).onHidingWidget()

    def on_timeout(self, *args, **kwargs):
        pass

    @property
    def jsCode(self):
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
        jsCode = super(WebTimeoutMixin, self).jsCode
        if self._run_timeout:
            jsCode.append(code)
        else:
            jsCode.append((5, '''$(document).ready(function(){$(".timeout-label").html(0);});'''))
        return jsCode


class WebTimeoutForwardMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self._experiment.userInterfaceController.moveForward()

class WebTimeoutCloseMixin(WebTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self.closeQuestion()

class HideButtonsMixin(object):
    def _onShowingWidget(self):
        self._experiment.userInterfaceController.layout.forwardEnabled = False
        self._experiment.userInterfaceController.layout.backwardEnabled = False
        self._experiment.userInterfaceController.layout.jumpListEnabled = False
        self._experiment.userInterfaceController.layout.finishDisabled = True

        super(HideButtonsMixin, self)._onShowingWidget()

    def _onHidingWidget(self):
        self._experiment.userInterfaceController.layout.forwardEnabled = True
        self._experiment.userInterfaceController.layout.backwardEnabled = True
        self._experiment.userInterfaceController.layout.jumpListEnabled = True
        self._experiment.userInterfaceController.layout.finishDisabled = False

        super(HideButtonsMixin, self)._onHidingWidget()

class QtTimeoutMixin(object):
    class Countdown(AsyncTask):
        def doInBackground(self,params):
            timeout, parent = params
            time.sleep(timeout)
            return parent

        def onPostExecute(self, parent):
            parent.callback()

    def __init__(self, timeout, **kwargs):
        super(QtTimeoutMixin, self).__init__(**kwargs)

        self._run_timeout = True
        self._timeout = timeout
        if settings.debugmode and settings.debug.reduceCountdown:
            self._timeout = int(settings.debug.reducedCountdownTime)

    def _onShowingWidget(self):
        super(QtTimeoutMixin, self)._onShowingWidget()

        if self._run_timeout:
            self._counter = self.Countdown()
            self._counter.execute((self._timeout,self))

    def _onHidingWidget(self):
        self._counter.cancel()
        self._run_timeout = False
        super(QtTimeoutMixin, self)._onHidingWidget()

    def callback(self, *args, **kwargs):
        self._run_timeout = False
        return self.on_timeout(*args, **kwargs)

    def on_timeout(self, *args, **kwargs):
        pass

class QtTimeoutForwardMixin(QtTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self._experiment.userInterfaceController.updateQtData()
        self._experiment.userInterfaceController.moveForward()

class QtTimeoutCloseMixin(QtTimeoutMixin):
    def on_timeout(self, *args, **kwargs):
        self._experiment.userInterfaceController.updateQtData()
        self.closeQuestion()
        self._experiment.userInterfaceController.render()



####################
# Questions with Mixins
####################

class WebTimeoutForwardQuestion(WebTimeoutForwardMixin, WebCompositeQuestion):
    pass

class WebTimeoutCloseQuestion(WebTimeoutCloseMixin, WebCompositeQuestion):
    pass

class QtTimeoutForwardQuestion(QtTimeoutForwardMixin, QtCompositeQuestion):
    pass

class QtTimeoutCloseQuestion(QtTimeoutCloseMixin, QtCompositeQuestion):
    pass
