"""
This test script contains regression tests of command-line tools,
gen_ngram.py, det_clone.py, tosl_clone.py, and exp_clone.py.

Use this script to detect inintended spec changes of these tools.

Warning: These tests may fail when any implementation detail is changed.
I've taken care about that these tests independent to the order of clones 
detected or the order of n-grams are generated.
However, this is far from a perfect solution for independability 
against implementation issues. 
In some case of implementation change, these tests will fail.
"""

import unittest

import os
import subprocess
#import sys
#import tempfile

J = os.path.join

PROG_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = J(os.path.dirname(__file__), "samplecode")
REF_DATA_DIR = J(DATA_DIR, "reference_data")

def read_text(filepath):
    with open(filepath, "rb") as f:
        return f.read().decode("utf-8")

def split_by_empty_line(lines):
    blocks = []
    curblock = []
    for L in lines:
        if not L:
            if curblock:
                blocks.append(curblock)
                curblock = []
        else:
            curblock.append(L)
    if curblock:
        blocks.append(curblock)
        curblock = []
    return blocks

class TestWithSampleCode(unittest.TestCase):
#    def setUp(self):
#        self.temp_dir = d = tempfile.mkdtemp()
#
#    def tearDown(self):
#        if self.temp_dir:
#            os.rmdir(self.temp_dir)

    def testGenNgram(self):
        text = subprocess.check_output(["python", J(PROG_DIR, "gen_ngram.py"), "-n", "6", DATA_DIR]).decode('utf-8')
        text_blocks = sorted(map(tuple, split_by_empty_line(text.split('\n'))))
        ref_text = read_text(J(REF_DATA_DIR, "ngram.txt"))
        ref_text_blocks = sorted(map(tuple, split_by_empty_line(ref_text.split('\n'))))
        self.assertSequenceEqual(text_blocks, ref_text_blocks)
    
    def testDetCodeClone(self):
        text = subprocess.check_output(["python", J(PROG_DIR, "det_clone.py"), J(REF_DATA_DIR, "ngram.txt")]).decode('utf-8')
        text_blocks = sorted(map(tuple, split_by_empty_line(text.split('\n'))))
        ref_text = read_text(J(REF_DATA_DIR, "clone-index.txt"))
        ref_text_blocks = sorted(map(tuple, split_by_empty_line(ref_text.split('\n'))))
        self.assertSequenceEqual(text_blocks, ref_text_blocks)
        
    def testToslCodeClone(self):
        text = subprocess.check_output(["python", J(PROG_DIR, "tosl_clone.py"), DATA_DIR, J(REF_DATA_DIR, "clone-index.txt")]).decode('utf-8')
        text_blocks = sorted(map(tuple, split_by_empty_line(text.split('\n'))))
        ref_text = read_text(J(REF_DATA_DIR, "clone-linenum.txt"))
        ref_text_blocks = sorted(map(tuple, split_by_empty_line(ref_text.split('\n'))))
        self.assertSequenceEqual(text_blocks, ref_text_blocks)
        
    def testExpClone(self):
        text = subprocess.check_output(["python", J(PROG_DIR, "exp_clone.py"), "-cdt", DATA_DIR, J(REF_DATA_DIR, "clone-index.txt")]).decode('utf-8')
        text_blocks = sorted(map(tuple, split_by_empty_line(text.split('\n'))))
        ref_text = read_text(J(REF_DATA_DIR, "clone-cdt-index.txt"))
        ref_text_blocks = sorted(map(tuple, split_by_empty_line(ref_text.split('\n'))))
        self.assertSequenceEqual(text_blocks, ref_text_blocks)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()