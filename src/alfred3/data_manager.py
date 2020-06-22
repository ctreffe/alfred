# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""
from __future__ import absolute_import

from builtins import object
from .exceptions import AlfredError


class DataManager(object):
    def __init__(self, experiment):
        self._experiment = experiment
        self._additional_data = {}

    def add_additional_data(self, key, value):
        self._additional_data[key] = value

    def get_additional_data_by_key(self, key):
        return self._additional_data[key]

    def get_data(self):
        data = self._experiment.page_controller.data
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_version"] = self._experiment.version
        data["exp_type"] = self._experiment.type
        data["start_time"] = self._experiment.start_time
        data["start_timestamp"] = self._experiment.start_timestamp
        data["exp_finished"] = self._experiment.finished
        data["exp_session"] = self._experiment.session
        data["exp_condition"] = self._experiment.condition
        data["exp_id"] = self._experiment.exp_id
        data["session_id"] = self._experiment.session_id
        data["session_status"] = self._experiment.session_status
        data["additional_data"] = self._additional_data
        data["alfred_version"] = self._experiment.alfred_version

        return data

    def find_experiment_data_by_uid(self, uid):
        data = self._experiment._page_controller.data
        return DataManager._find_by_uid(data, uid)

    def find_additional_data_by_key_and_uid(self, key, uid):
        data = self._additional_data[key]
        return DataManager._find_by_uid(data, uid)

    @staticmethod
    def _find_by_uid(data, uid):
        def worker(data, uid):
            if data["uid"] == uid:
                return data
            elif "subtree_data" in data:

                for item in data["subtree_data"]:
                    try:
                        d = worker(item, uid)
                        return d
                    except Exception:
                        if item == data["subtree_data"][-1]:
                            raise AlfredError("did not find uuid in tree")
                raise AlfredError("Custom Error")
            else:
                raise AlfredError("did not find uuid in tree")

        return worker(data, uid)
