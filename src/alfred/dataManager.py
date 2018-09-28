# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>
"""

from exceptions import AlfredError

class DataManager(object):
    def __init__(self, experiment):
        self._experiment = experiment
        self._additionalData = {}

    def addAdditionalData(self, key, value):
        self._additionalData[key] = value

    def getAddionalDataByKey(self, key):
        return self._additionalData[key]

    def getData(self):
        data = self._experiment.questionController.data
        data['expName'] = self._experiment.name
        data['expVersion'] = self._experiment.version
        data['expType'] = self._experiment.type
        data['start_time'] = self._experiment._start_time
        data['startTime'] = self._experiment.startTimeStamp
        data['expFinished'] = self._experiment.finished
        data['expTestCondition'] = self._experiment.testCondition
        data['expUuid'] = self._experiment.uuid
        data['additionalData'] = self._additionalData

        return data

    def findExperimentDataByUid(self, uid):
        data = self._experiment._questionController.data
        return DataManager._findByUid(data, uid)

    def findAdditionalDataByKeyAndUid(self, key, uid):
        data = self._additionalData[key]
        return DataManager._findByUid(data, uid)

    @staticmethod
    def _findByUid(data, uid):
        def worker(data, uid):
            if data['uid'] == uid:
                return data
            elif data.has_key('subtreeData'):
                
                for item in data['subtreeData']:
                    try:
                        d = worker(item, uid)
                        return d
                    except:
                        if item == data['subtreeData'][-1]:
                            raise AlfredError("did not find uuid in tree")
                raise AlfredError("Custom Error")
            else:
                raise AlfredError("did not find uuid in tree")
        return worker(data, uid)

