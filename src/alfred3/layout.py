# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

.. todo:: Beim Modulimport wird ein Fehler angezeigt. Gibt es wirklich eine Klasse *Template* in **jinja2**?
"""
from __future__ import absolute_import

import os.path
from abc import ABCMeta, abstractmethod
from builtins import map, object, range

from future.utils import with_metaclass
from jinja2 import Environment, PackageLoader

from ._core import package_path

jinja_env = Environment(loader=PackageLoader("alfred3", "templates"))


class Layout(with_metaclass(ABCMeta, object)):
    def __init__(self):
        self._experiment = None
        self._ui_controller = None
        self._backward_text = None
        self._forward_text = None
        self._finish_text = None
        self._backward_enabled = True
        self._forward_enabled = True
        self._finished_diasbled = False
        self._jump_list_enabled = True
        self._jump_list = []

    def activate(self, experiment, ui_controller):
        self._experiment = experiment
        self._backward_text = self._experiment.config.get("navigation", "backward")
        self._forward_text = self._experiment.config.get("navigation", "forward")
        self._finish_text = self._experiment.config.get("navigation", "finish")
        self._ui_controller = ui_controller

    def deactivate(self):
        self._experiment = None
        self._ui_controller = None

    @abstractmethod
    def render(self, widget):
        pass

    @property
    def backward_enabled(self):
        return self._backward_enabled

    @backward_enabled.setter
    def backward_enabled(self, b):
        self._backward_enabled = b

    @property
    def forward_enabled(self):
        return self._forward_enabled

    @forward_enabled.setter
    def forward_enabled(self, b):
        self._forward_enabled = b

    @property
    def finish_disabled(self):
        return self._finished_diasbled

    @finish_disabled.setter
    def finish_disabled(self, b):
        self._finished_diasbled = b

    @property
    def backward_text(self):
        return self._backward_text

    @backward_text.setter
    def backward_text(self, text):
        self._backward_text = text

    @property
    def forward_text(self):
        return self._forward_text

    @forward_text.setter
    def forward_text(self, text):
        self._forward_text = text

    @property
    def finish_text(self):
        return self._finish_text

    @finish_text.setter
    def finish_text(self, text):
        self._finish_text = text

    @property
    def jump_list_enabled(self):
        return self._jump_list_enabled

    @jump_list_enabled.setter
    def jump_list_enabled(self, b):
        self._jump_list_enabled = b


class BaseWebLayout(Layout):
    def __init__(self):
        super(BaseWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template("base_layout.html")

    def activate(self, experiment, ui_controller):
        super(BaseWebLayout, self).activate(experiment, ui_controller)
        # add css files
        self._style_urls.append(
            (
                99,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/base_web_layout.css"),
                    content_type="text/css",
                ),
            )
        )
        self._style_urls.append(
            (
                1,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/bootstrap.min.css"),
                    content_type="text/css",
                ),
            )
        )
        self._style_urls.append(
            (
                2,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/jquery-ui.css"),
                    content_type="text/css",
                ),
            )
        )
        # self._style_urls.append(self._ui_controller.add_static_file(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append(
            (
                0o1,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/jquery-1.8.3.min.js"),
                    content_type="text/javascript",
                ),
            )
        )
        self._js_urls.append(
            (
                0o2,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/bootstrap.min.js"),
                    content_type="text/javascript",
                ),
            )
        )
        self._js_urls.append(
            (
                0o3,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/jquery-ui.js"),
                    content_type="text/javascript",
                ),
            )
        )

        self._js_urls.append(
            (
                10,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/baseweblayout.js"),
                    content_type="text/javascript",
                ),
            )
        )

        self._logo_url = self._ui_controller.add_static_file(
            os.path.join(package_path(), "static/img/alfred_logo.png"), content_type="image/png"
        )

    @property
    def css_code(self):
        return []

    @property
    def css_urls(self):
        return self._style_urls

    @property
    def javascript_code(self):
        return []

    @property
    def javascript_urls(self):
        return self._js_urls

    def render(self):

        d = {}
        d["logo_url"] = self._logo_url
        d["widget"] = self._experiment.page_controller.current_page.web_widget

        if self._experiment.page_controller.current_title:
            d["title"] = self._experiment.page_controller.current_title

        if self._experiment.page_controller.current_subtitle:
            d["subtitle"] = self._experiment.page_controller.current_subtitle

        if self._experiment.page_controller.current_status_text:
            d["statustext"] = self._experiment.page_controller.current_status_text

        if (
            not self._experiment.page_controller.current_page.can_display_corrective_hints_in_line
            and self._experiment.page_controller.current_page.corrective_hints
        ):
            d["corrective_hints"] = self._experiment.page_controller.current_page.corrective_hints

        if self.backward_enabled and self._experiment.page_controller.can_move_backward:
            d["backward_text"] = self.backward_text

        if self.forward_enabled:
            if self._experiment.page_controller.can_move_forward:
                d["forward_text"] = self.forward_text
            else:
                if not self._finished_diasbled:
                    d["finish_text"] = self.finish_text

        if self.jump_list_enabled and self._experiment.page_controller.jumplist:
            jmplist = self._experiment.page_controller.jumplist
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = ".".join(map(str, jmplist[i][0]))
            d["jump_list"] = jmplist

        messages = self._experiment.message_manager.get_messages()
        if messages:
            for message in messages:
                message.level = (
                    "" if message.level == "warning" else "alert-" + message.level
                )  # level to bootstrap
            d["messages"] = messages

        return self._template.render(d)

    @property
    def backward_link(self):
        return self._backward_link

    @backward_link.setter
    def backward_link(self, link):
        self._backward_link = link

    @property
    def forward_link(self):
        return self._forward_link

    @forward_link.setter
    def forward_link(self, link):
        self._forward_link = link


class GoeWebLayout(Layout):
    def __init__(self):
        super(GoeWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template("goe_layout.html")

    def activate(self, experiment, ui_controller):
        super(GoeWebLayout, self).activate(experiment, ui_controller)
        # add css files
        self._style_urls.append(
            (
                99,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/goe_web_layout.css"),
                    content_type="text/css",
                ),
            )
        )
        self._style_urls.append(
            (
                1,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/bootstrap.min.css"),
                    content_type="text/css",
                ),
            )
        )
        self._style_urls.append(
            (
                2,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/css/jquery-ui.css"),
                    content_type="text/css",
                ),
            )
        )
        # self._style_urls.append(self._ui_controller.add_static_file(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append(
            (
                0o1,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/jquery-1.8.3.min.js"),
                    content_type="text/javascript",
                ),
            )
        )
        self._js_urls.append(
            (
                0o2,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/bootstrap.min.js"),
                    content_type="text/javascript",
                ),
            )
        )
        self._js_urls.append(
            (
                0o3,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/jquery-ui.js"),
                    content_type="text/javascript",
                ),
            )
        )

        self._js_urls.append(
            (
                10,
                self._ui_controller.add_static_file(
                    os.path.join(package_path(), "static/js/baseweblayout.js"),
                    content_type="text/javascript",
                ),
            )
        )

        self._logo_url = self._ui_controller.add_static_file(
            os.path.join(package_path(), "static/img/uni_goe_logo.png"), content_type="image/png"
        )

    @property
    def css_code(self):
        return []

    @property
    def css_urls(self):
        return self._style_urls

    @property
    def javascript_code(self):
        return []

    @property
    def javascript_urls(self):
        return self._js_urls

    def render(self):

        d = {}
        d["logo_url"] = self._logo_url
        d["widget"] = self._experiment.page_controller.current_page.web_widget

        if self._experiment.page_controller.current_title:
            d["title"] = self._experiment.page_controller.current_title

        if self._experiment.page_controller.current_subtitle:
            d["subtitle"] = self._experiment.page_controller.current_subtitle

        if self._experiment.page_controller.current_status_text:
            d["statustext"] = self._experiment.page_controller.current_status_text

        if (
            not self._experiment.page_controller.current_page.can_display_corrective_hints_in_line
            and self._experiment.page_controller.current_page.corrective_hints
        ):
            d["corrective_hints"] = self._experiment.page_controller.current_page.corrective_hints

        if self.backward_enabled and self._experiment.page_controller.can_move_backward:
            d["backward_text"] = self.backward_text

        if self.forward_enabled:
            if self._experiment.page_controller.can_move_forward:
                d["forward_text"] = self.forward_text
            else:
                if not self._finished_diasbled:
                    d["finish_text"] = self.finish_text

        if self.jump_list_enabled and self._experiment.page_controller.jumplist:
            jmplist = self._experiment.page_controller.jumplist
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = ".".join(map(str, jmplist[i][0]))
            d["jump_list"] = jmplist

        messages = self._experiment.message_manager.get_messages()
        if messages:
            for message in messages:
                message.level = (
                    "" if message.level == "warning" else "alert-" + message.level
                )  # level to bootstrap
            d["messages"] = messages

        return self._template.render(d)

    @property
    def backward_link(self):
        return self._backward_link

    @backward_link.setter
    def backward_link(self, link):
        self._backward_link = link

    @property
    def forward_link(self):
        return self._forward_link

    @forward_link.setter
    def forward_link(self, link):
        self._forward_link = link
