# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

.. todo:: Beim Modulimport wird ein Fehler angezeigt. Gibt es wirklich eine Klasse *Template* in **jinja2**?
'''
from __future__ import absolute_import


from builtins import map
from builtins import range
from builtins import object
import os.path
from abc import ABCMeta, abstractmethod
from jinja2 import Environment, PackageLoader
from future.utils import with_metaclass

from ._core import package_path

jinja_env = Environment(loader=PackageLoader('alfred', 'templates'))


class Layout(with_metaclass(ABCMeta, object)):
    def __init__(self):
        self._experiment = None
        self._uiController = None
        self._backwardText = u"Zurück"
        self._forwardText = u"Weiter"
        self._finishText = u"Beenden"
        self._backwardEnabled = True
        self._forwardEnabled = True
        self._finishedDisabled = False
        self._jumpListEnabled = True
        self._jumpList = []

    def activate(self, experiment, uiController):
        self._experiment = experiment
        self._uiController = uiController

    def deactivate(self):
        self._experiment = None
        self._uiController = None

    @abstractmethod
    def render(self, widget):
        pass

    @property
    def backwardEnabled(self):
        return self._backwardEnabled

    @backwardEnabled.setter
    def backwardEnabled(self, b):
        self._backwardEnabled = b

    @property
    def forwardEnabled(self):
        return self._forwardEnabled

    @forwardEnabled.setter
    def forwardEnabled(self, b):
        self._forwardEnabled = b

    @property
    def finishDisabled(self):
        return self._finishedDisabled

    @finishDisabled.setter
    def finishDisabled(self, b):
        self._finishedDisabled = b

    @property
    def backwardText(self):
        return self._backwardText

    @backwardText.setter
    def backwardText(self, text):
        self._backwardText = text

    @property
    def forwardText(self):
        return self._forwardText

    @forwardText.setter
    def forwardText(self, text):
        self._forwardText = text

    @property
    def finishText(self):
        return self._finishText

    @finishText.setter
    def finishText(self, text):
        self._finishText = text

    @property
    def jumpListEnabled(self):
        return self._jumpListEnabled

    @jumpListEnabled.setter
    def jumpListEnabled(self, b):
        self._jumpListEnabled = b


class BaseWebLayout(Layout):

    def __init__(self):
        super(BaseWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template('base_layout.html')

    def activate(self, experiment, uiController):
        super(BaseWebLayout, self).activate(experiment, uiController)
        # add css files
        self._style_urls.append((99, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/base_web_layout.css'), content_type="text/css")))
        self._style_urls.append((1, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/bootstrap.min.css'), content_type="text/css")))
        self._style_urls.append((2, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/jquery-ui.css'), content_type="text/css")))
        # self._style_urls.append(self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append((0o1,
                              self._uiController.addStaticFile(
                                  os.path.join(package_path(), 'static/js/jquery-1.8.3.min.js'),
                                  content_type="text/javascript")
                              ))
        self._js_urls.append((0o2, self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/bootstrap.min.js'), content_type="text/javascript")))
        self._js_urls.append((0o3, self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/jquery-ui.js'), content_type="text/javascript")))

        self._js_urls.append((10,
                              self._uiController.addStaticFile(
                                  os.path.join(package_path(), 'static/js/baseweblayout.js'),
                                  content_type="text/javascript")
                              ))

        self._logo_url = self._uiController.addStaticFile(os.path.join(package_path(), 'static/img/alfred_logo.png'), content_type="image/png")

    @property
    def cssCode(self):
        return []

    @property
    def cssURLs(self):
        return self._style_urls

    @property
    def javascriptCode(self):
        return []

    @property
    def javascriptURLs(self):
        return self._js_urls

    def render(self):

        d = {}
        d['logo_url'] = self._logo_url
        d['widget'] = self._experiment.questionController.currentQuestion.webWidget

        if self._experiment.questionController.currentTitle:
            d['title'] = self._experiment.questionController.currentTitle

        if self._experiment.questionController.currentSubtitle:
            d['subtitle'] = self._experiment.questionController.currentSubtitle

        if self._experiment.questionController.currentStatustext:
            d['statustext'] = self._experiment.questionController.currentStatustext

        if not self._experiment.questionController.currentQuestion.canDisplayCorrectiveHintsInline \
                and self._experiment.questionController.currentQuestion.correctiveHints:
            d['corrective_hints'] = self._experiment.questionController.currentQuestion.correctiveHints

        if self.backwardEnabled and self._experiment.questionController.canMoveBackward:
            d['backward_text'] = self.backwardText

        if self.forwardEnabled:
            if self._experiment.questionController.canMoveForward:
                d['forward_text'] = self.forwardText
            else:
                if not self._finishedDisabled:
                    d['finish_text'] = self.finishText

        if self.jumpListEnabled and self._experiment.questionController.jumplist:
            jmplist = self._experiment.questionController.jumplist
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = '.'.join(map(str, jmplist[i][0]))
            d['jumpList'] = jmplist

        messages = self._experiment.messageManager.getMessages()
        if messages:
            for message in messages:
                message.level = '' if message.level == 'warning' else 'alert-' + message.level  # level to bootstrap
            d['messages'] = messages

        return self._template.render(d)

    @property
    def backwardLink(self):
        return self._backwardLink

    @backwardLink.setter
    def backwardLink(self, link):
        self._backwardLink = link

    @property
    def forwardLink(self):
        return self._forwardLink

    @forwardLink.setter
    def forwardLink(self, link):
        self._forwardLink = link


class GoeWebLayout(Layout):
    def __init__(self):
        super(GoeWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template('goe_layout.html')

    def activate(self, experiment, uiController):
        super(GoeWebLayout, self).activate(experiment, uiController)
        # add css files
        self._style_urls.append((99, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/goe_web_layout.css'), content_type="text/css")))
        self._style_urls.append((1, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/bootstrap.min.css'), content_type="text/css")))
        self._style_urls.append((2, self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/jquery-ui.css'), content_type="text/css")))
        # self._style_urls.append(self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append((0o1,
                              self._uiController.addStaticFile(
                                  os.path.join(package_path(), 'static/js/jquery-1.8.3.min.js'),
                                  content_type="text/javascript")
                              ))
        self._js_urls.append((0o2, self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/bootstrap.min.js'), content_type="text/javascript")))
        self._js_urls.append((0o3, self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/jquery-ui.js'), content_type="text/javascript")))

        self._js_urls.append((10,
                              self._uiController.addStaticFile(
                                  os.path.join(package_path(), 'static/js/baseweblayout.js'),
                                  content_type="text/javascript")
                              ))

        self._logo_url = self._uiController.addStaticFile(os.path.join(package_path(), 'static/img/uni_goe_logo.png'), content_type="image/png")

    @property
    def cssCode(self):
        return []

    @property
    def cssURLs(self):
        return self._style_urls

    @property
    def javascriptCode(self):
        return []

    @property
    def javascriptURLs(self):
        return self._js_urls

    def render(self):

        d = {}
        d['logo_url'] = self._logo_url
        d['widget'] = self._experiment.questionController.currentQuestion.webWidget

        if self._experiment.questionController.currentTitle:
            d['title'] = self._experiment.questionController.currentTitle

        if self._experiment.questionController.currentSubtitle:
            d['subtitle'] = self._experiment.questionController.currentSubtitle

        if self._experiment.questionController.currentStatustext:
            d['statustext'] = self._experiment.questionController.currentStatustext

        if not self._experiment.questionController.currentQuestion.canDisplayCorrectiveHintsInline \
                and self._experiment.questionController.currentQuestion.correctiveHints:
            d['corrective_hints'] = self._experiment.questionController.currentQuestion.correctiveHints

        if self.backwardEnabled and self._experiment.questionController.canMoveBackward:
            d['backward_text'] = self.backwardText

        if self.forwardEnabled:
            if self._experiment.questionController.canMoveForward:
                d['forward_text'] = self.forwardText
            else:
                if not self._finishedDisabled:
                    d['finish_text'] = self.finishText

        if self.jumpListEnabled and self._experiment.questionController.jumplist:
            jmplist = self._experiment.questionController.jumplist
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = '.'.join(map(str, jmplist[i][0]))
            d['jumpList'] = jmplist

        messages = self._experiment.messageManager.getMessages()
        if messages:
            for message in messages:
                message.level = '' if message.level == 'warning' else 'alert-' + message.level  # level to bootstrap
            d['messages'] = messages

        return self._template.render(d)

    @property
    def backwardLink(self):
        return self._backwardLink

    @backwardLink.setter
    def backwardLink(self, link):
        self._backwardLink = link

    @property
    def forwardLink(self):
        return self._forwardLink

    @forwardLink.setter
    def forwardLink(self, link):
        self._forwardLink = link
