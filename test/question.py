import unittest
from alfred import Experiment
from alfred._core import QuestionCore
from alfred.question import Question
from alfred.questionGroup import QuestionGroup
from alfred.exceptions import MoveError


class TestQuestionCore(unittest.TestCase):


    def test_tagAndUid(self):
        tag = '123'
        uid = '321'

        qCore = QuestionCore()
        self.assertIsNone(qCore.tag)
        self.assertIsNotNone(qCore.uid)

        qCore.tag = tag
        self.assertEqual(qCore.tag, tag)
        with self.assertRaises(ValueError):
            qCore.tag = tag + 'foobar'

        with self.assertRaises(TypeError):
            qCore.tag = 2

        # key word constructor
        qCore = QuestionCore(tag=tag, uid=uid)
        self.assertEqual(qCore.tag, tag)
        self.assertEqual(qCore.uid, uid)

        self.assertEqual(qCore.data['tag'], tag)
        self.assertEqual(qCore.data['uid'], uid)

    def test_shouldBeShown(self):
        qCore = QuestionCore()
        self.assertTrue(qCore.shouldBeShown)

        qCore.shouldBeShown = False
        self.assertFalse(qCore.shouldBeShown)
        qCore.shouldBeShown = True
        self.assertTrue(qCore.shouldBeShown)

        with self.assertRaises(TypeError):
            qCore.shouldBeShown = 2



    def test_jumpable(self):
        qCore = QuestionCore()
        self.assertFalse(qCore.isJumpable)

        qCore.isJumpable = True
        self.assertFalse(qCore.isJumpable)

        qCore.jumptext = "jumptext"
        self.assertTrue(qCore.isJumpable)

        qCore.isJumpable = False
        self.assertFalse(qCore.isJumpable)

    def test_title(self):
        qCore = QuestionCore(title='title')
        self.assertEqual(qCore.title, 'title')

        qCore.title = 'foobar'
        self.assertEqual(qCore.title, 'foobar')

    def test_subtitle(self):
        qCore = QuestionCore(subtitle='subtitle')
        self.assertEqual(qCore.subtitle, 'subtitle')

        qCore.subtitle = 'foobar'
        self.assertEqual(qCore.subtitle, 'foobar')

    def test_statustext(self):
        qCore = QuestionCore(statustext='statustext')
        self.assertEqual(qCore.statustext, 'statustext')

        qCore.statustext = 'foobar'
        self.assertEqual(qCore.statustext, 'foobar')

class TestQuestionGroup(unittest.TestCase):

    def setUp(self):
        self.group = QuestionGroup(tag = 'tag', uid = 'uid')

        self.q0 = Question()
        self.q1 = Question(tag='tag')
        self.q2 = Question()
        self.q2.shouldBeShown = False
        self.q3 = Question()
        self.q4 = QuestionGroup()
        self.q5 = Question()

        self.q41 = Question()
        self.q4.appendItem(Question())
        self.q4.appendItem(self.q41)
        self.q4.appendItem(Question())

        self.group.appendItem(self.q0)
        self.group.appendItem(self.q1)
        self.group.appendItem(self.q2)
        self.group.appendItem(self.q3)
        self.group.appendItem(self.q4)
        self.group.appendItem(self.q5)

        self.group.generateUnsetTagsInSubtree()

#    def test_jumplist(self):
#        rootGroup = QuestionGroup(isJumpable=True, jumptext='rootGroup')
#        q0 = Question(isJumpable=True, jumptext='q0')
#        q1 = Question(isJumpable=True, jumptext='q1')
#        subGroup = QuestionGroup(isJumpable=True, jumptext='subGroup')
#        q20 = Question(isJumpable=True, jumptext='q20')
#
#        rootGroup.appendItems(q0, q1, subGroup)
#        subGroup.appendItem(q20)
#
#        self.assertEqual([([], 'rootGroup'), ([0], 'q0'), ([1], 'q1'), ([2], 'subGroup'), ([2,0], 'q20')], rootGroup.jumplist)


    def test_movement(self):
        self.group.moveToFirst()
        self.assertEqual(self.group.currentQuestion, self.q0)

        self.group.moveForward()
        self.assertEqual(self.group.currentQuestion, self.q1)

        self.group.moveForward()
        self.assertEqual(self.group.currentQuestion, self.q3)

        self.group.moveForward()
        self.group.moveForward()
        self.assertEqual(self.group.currentQuestion, self.q41)

        self.group.moveToLast()
        self.assertEqual(self.group.currentQuestion, self.q5)

        self.group.moveToPosition([4,1])
        self.assertEqual(self.group.currentQuestion, self.q41)

        self.group.moveToPosition([0])
        self.assertFalse(self.group.canMoveBackward)

        self.group.moveToLast()
        self.assertTrue(self.group.canMoveBackward)
        self.assertFalse(self.group.canMoveForward)

        self.group.moveToFirst()
        self.assertRaises(MoveError, self.group.moveBackward)

        self.group.moveToLast()
        self.assertRaises(MoveError, self.group.moveForward)

    def test_shouldBeShown(self):
        group = QuestionGroup(tag = 'tag', uid = 'uid')
        q0 = Question()
        group.appendItem(q0)

        self.assertTrue(group.shouldBeShown)

        group.shouldBeShown = False
        self.assertFalse(group.shouldBeShown)

        group.shouldBeShown = True
        self.assertTrue(group.shouldBeShown)

        q0.shouldBeShown = False
        self.assertFalse(group.shouldBeShown)

        q0.shouldBeShown = True
        self.assertTrue(group.shouldBeShown)



    def test_tags(self):
        self.assertEqual(self.q0.tag, '0')
        self.assertEqual(self.q1.tag, 'tag')
        self.assertEqual(self.q5.tag, '5')
        self.assertEqual(self.q41.tag, '1')


    def test_data(self):
        self.assertEqual(self.group.data['subtreeData'][0], self.q0.data)
        self.assertEqual(self.group.data['subtreeData'][4], self.q4.data)


