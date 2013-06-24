#coding: utf-8

import unittest

import os.path as p
import subprocess
import sys

PATH = p.join(p.dirname(p.abspath(__file__)), '..', 'src')
sys.path.insert(0, PATH)

from _version_data import VERSION

class TestCommandline(unittest.TestCase):
    def testVersionInfo(self):
        def check_version(script):
            det_clone_version_str = subprocess.check_output(' '.join(["python", p.join(PATH, script), "--version"]), 
                    stderr=subprocess.STDOUT, shell=True)
            self.assertEqual(det_clone_version_str, '%s %s\n' % (script, VERSION))
        check_version("det_clone.py")
        check_version("exp_clone.py")
        check_version("gen_ngram.py")
        check_version("tosl_clone.py")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()