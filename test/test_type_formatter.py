#coding: utf-8

import unittest
import doctest

import os
import os.path as p
import sys

sys.path.insert(0, p.join(p.dirname(p.abspath(__file__)), '..', 'src'))

import type_formatter as tf

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(tf))
    return tests

class TestTypeFormatter(unittest.TestCase):
    def testValueTypes(self):
        self.assertEqual(tf.format_type('int'), 'I')
        self.assertEqual(tf.format_type('boolean'), 'Z')
        self.assertEqual(tf.format_type('byte'), 'B')
        self.assertEqual(tf.format_type('short'), 'S')
        self.assertEqual(tf.format_type('long'), 'J')
        self.assertEqual(tf.format_type('float'), 'F')
        self.assertEqual(tf.format_type('double'), 'D')
        self.assertEqual(tf.format_type('void'), 'V')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
