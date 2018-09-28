import unittest
from alfred import Experiment
from alfred._core import QuestionCore
import alfred.helpmates.filterFunctions as ff

class TestQuestionCore(unittest.TestCase):
    def setUp(self):
        self.qCore = QuestionCore()
        self.exp = Experiment('web', 'name')
        self.qCore.addedToExperiment(self.exp)

    def test_and_(self):

        f_t = ff.and_(lambda x: True, lambda x: True)
        f_f = ff.and_(lambda x: True, lambda x: False)

        self.assertTrue(f_t(self.exp))
        self.assertFalse(f_f(self.exp))

    def test_or_(self):
        f_t = ff.or_(lambda x: False, lambda x: True)
        f_f = ff.or_(lambda x: False, lambda x: False)

        self.assertTrue(f_t(self.exp))
        self.assertFalse(f_f(self.exp))

    def test_not_(self):
        f_t = ff.not_(lambda x: False)
        f_f = ff.not_(lambda x: True)

        self.assertTrue(f_t(self.exp))
        self.assertFalse(f_f(self.exp))

    def test_QuestionCore(self):
        f_t = ff.and_(lambda exp: exp.name == 'name', lambda exp: exp.type == 'web')
        f_f = ff.and_(lambda exp: exp.name == 'noName', lambda exp: exp.type == 'web')

        self.assertTrue(self.qCore.shouldBeShown)

        self.qCore.setShouldBeShownFilterFunction(f_f)
        self.assertFalse(self.qCore.shouldBeShown)

        self.qCore.removeShouldBeShownFilterFunction()
        self.assertTrue(self.qCore.shouldBeShown)

        self.qCore.setShouldBeShownFilterFunction(f_t)
        self.assertTrue(self.qCore.shouldBeShown)
