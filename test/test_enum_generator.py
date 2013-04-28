#coding: utf-8

import unittest

import os
import os.path as p
import sys

sys.path.insert(0, p.join(p.dirname(p.abspath(__file__)), '..', 'src'))

import enum_generator as eg

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

class TestEnumGenerator(unittest.TestCase):
    def testEmptyEnum(self):
        e = eg.EnumGenerator()
        self.assertSequenceEqual(e.get_strs(), [])
        with self.assertRaises(eg.EmptyEnumString):
            e.to_int('')
            
    def testSimpleEnum(self):
        names = 'a,b,c'.split(',')
        e = eg.EnumGenerator(names)
        self.assertSequenceEqual(e.get_strs(), names)
        self.assertEquals(e.to_int('a'), 1)
        self.assertEquals(e.to_int('b'), 2)
        self.assertEquals(e.to_int('c'), 3)
        self.assertEquals(e.to_str(e.to_int('a')), 'a')
        self.assertEquals(e.to_str(e.to_int('b')), 'b')
        self.assertEquals(e.to_str(e.to_int('c')), 'c')
        
    def testAddName(self):
        e = eg.EnumGenerator()
        self.assertSequenceEqual(e.get_strs(), [])
        e.add_name('b')
        self.assertSequenceEqual(e.get_strs(), ['b'])
        e.add_name('a')
        self.assertSequenceEqual(e.get_strs(), ['b', 'a'])
        e.add_name('c')
        self.assertSequenceEqual(e.get_strs(), ['b', 'a', 'c'])
        with self.assertRaises(eg.DuplicatedEnumString):
            e.add_name('c')
    
    def testLookupStr(self):
        names = 'a,b,c'.split(',')
        e = eg.EnumGenerator(names)
        self.assertEqual(e.lookup_str('a'), 1)
        self.assertEqual(e.lookup_str('b'), 2)
        self.assertEqual(e.lookup_str('c'), 3)
        self.assertEqual(e.lookup_str('d'), -1)
    
    def testImplicitlyAddNameWithToInt(self):
        e = eg.EnumGenerator()
        self.assertSequenceEqual(e.get_strs(), [])
        self.assertEquals(e.to_int('c'), 1)
        self.assertEquals(e.to_int('b'), 2)
        self.assertEquals(e.to_int('a'), 3)
        self.assertSequenceEqual(e.get_strs(), 'c,b,a'.split(','))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
