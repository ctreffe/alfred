import unittest
import alfred.settings as settings

class Test_DictObj(unittest.TestCase):
	def test_dict_obj(self):
		d = settings._DictObj()

		l = [1, 4.0, "Hello", object(), u"Hello World", [1,2,3,4]]
		for v in l:
			d.test = v
			self.assertEqual(d.test, v)