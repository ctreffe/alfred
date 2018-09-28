#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, unittest

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(os.path.dirname(__file__), "."), '*.py')
    unittest.TextTestRunner().run(suite)



