import unittest
from alfred import Experiment

class TextExperiment(unittest.TestCase):
    def test_constructor1(self):
        with self.assertRaises(ValueError):
            Experiment('web', 'name', '')

    def test_constructor2(self):
        with self.assertRaises(ValueError):
            Experiment('web', '')

    def test_constructor3(self):
        with self.assertRaises(ValueError):
            Experiment('web', 1)

    def test_constructor4(self):
        with self.assertRaises(ValueError):
            Experiment('not_valid', 'test')

    def test_name(self):
        name = 'name'
        e = Experiment('web', name)
        self.assertEqual(name, e.name)

    def test_version(self):
        v = '2.1a'
        e = Experiment('web', 'name', v)
        self.assertEqual(v, e.version)

    def test_type(self):
        self.assertEqual('web', Experiment('web', 'name').type)
        #self.assertEqual('qt', Experiment('qt', 'name').type)

    def test_readonly_properties(self):
        e = Experiment('web', 'name')
        with self.assertRaises(AttributeError):
            e.type = 'foo'
        with self.assertRaises(AttributeError):
            e.name = 'foo'
        with self.assertRaises(AttributeError):
            e.version = 'foo'
        with self.assertRaises(AttributeError):
            e.savingAgentController = None
        with self.assertRaises(AttributeError):
            e.questionController = None
        with self.assertRaises(AttributeError):
            e.dataManager = None
