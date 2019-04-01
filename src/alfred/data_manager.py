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
        self._additionalData = {}

    def add_additional_data(self, key, value):
        self._additionalData[key] = value

    def get_additional_data_by_key(self, key):
        return self._additionalData[key]

    def get_data(self):
        data = self._experiment.question_controller.data
        data['expAuthorMail'] = self._experiment.author_mail
        data['expName'] = self._experiment.name
        data['expVersion'] = self._experiment.version
        data['expType'] = self._experiment.type
        data['start_time'] = self._experiment._start_time
        data['startTime'] = self._experiment.start_timestamp
        data['expFinished'] = self._experiment.finished
        data['expTestCondition'] = self._experiment.test_condition
        data['expUuid'] = self._experiment.uuid
        data['additionalData'] = self._additionalData

        return data

    def find_experiment_data_by_uid(self, uid):
        data = self._experiment._questionController.data
        return DataManager._find_by_uid(data, uid)

    def find_additional_data_by_key_and_uid(self, key, uid):
        data = self._additionalData[key]
        return DataManager._find_by_uid(data, uid)

    @staticmethod
    def _find_by_uid(data, uid):
        def worker(data, uid):
            if data['uid'] == uid:
                return data
            elif 'subtreeData' in data:

                for item in data['subtreeData']:
                    try:
                        d = worker(item, uid)
                        return d
                    except Exception:
                        if item == data['subtreeData'][-1]:
                            raise AlfredError("did not find uuid in tree")
                raise AlfredError("Custom Error")
            else:
                raise AlfredError("did not find uuid in tree")
        return worker(data, uid)
