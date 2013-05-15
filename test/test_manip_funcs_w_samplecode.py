#coding: utf-8

import unittest

import os.path as p
import sys

sys.path.insert(0, p.join(p.dirname(p.abspath(__file__)), '..', 'src'))

J = p.join

PROG_DIR = p.join(p.dirname(p.abspath(__file__)), '..', 'src')
DATA_DIR = J(p.dirname(__file__), "samplecode")
REF_DATA_DIR = J(DATA_DIR, "reference_data")

import asm_manip as am
import clonefile_manip as cm

class TestManipFuncsWSamplecode(unittest.TestCase):
    def testReadSamplecodeAsm(self):
        for asmfile, lines in am.asm_filetext_iter(DATA_DIR):
            self.assertEqual(asmfile, J(DATA_DIR, "ShowWeekdayR.asm"))

    def testReadSamplecodeClone(self):
        for tag, value in cm.read_clone_file_iter(J(DATA_DIR, "reference_data", "clone-index.txt")):
            pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()