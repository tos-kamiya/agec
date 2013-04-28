#coding: utf-8

import unittest

import os
import os.path as p
import sys

sys.path.insert(0, p.join(p.dirname(p.abspath(__file__)), '..', 'src'))

import clonefile_manip as cm

class TestOptionHolder(unittest.TestCase):
    def testEmptyOptionHolder(self):
        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        t = oh.format()
        self.assertSequenceEqual(t, [
            '# --ngram-size=-1', 
            '# --max-branch=-1', 
            '# --max-call-depth=-1', 
            '# --max-method-definition=-1'
         ])

    def testUpdate(self):
        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        self.assertEqual(oh.ngram_size, -1)
        oh.update("ngram-size", 3)
        self.assertEqual(oh.ngram_size, 3)
        self.assertEqual(oh.get("ngram-size"), 3)

        self.assertEqual(oh.max_call_depth, -1)
        oh.update("max-call-depth", 4)
        self.assertEqual(oh.max_call_depth, 4)
        
        self.assertEqual(oh.exclude, [])
        oh.update("exclude", "org/hoge/app/AClass")
        self.assertEqual(oh.exclude, ["org/hoge/app/AClass"])
        oh.update("exclude", "org/hoge/app/BClass")
        self.assertEqual(oh.exclude, ["org/hoge/app/AClass", "org/hoge/app/BClass"])
        
        self.assertTrue(not oh.include_ctors)
        oh.update("include-ctors", True)
        self.assertTrue(oh.include_ctors)

    def testScan(self):
        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        oh.update("ngram-size", 3)
        oh.update("max-call-depth", 4)
        oh.update("exclude", "org/hoge/app/AClass")
        oh.update("exclude", "org/hoge/app/BClass")
        oh.update("include-ctors", True)
        buf = oh.format()
        
        ph = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        for L in buf:
            ph.scan_update(L)
        buf2 = ph.format()
        
        self.assertSequenceEqual(buf2, buf)

    def testDelete(self):
        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        oh.delete("ngram-size")
        t = oh.format()
        self.assertSequenceEqual(t, [
            '# --max-branch=-1', 
            '# --max-call-depth=-1', 
            '# --max-method-definition=-1'
         ])

EmptyDataLines = """
# --ngram-size=6
# --max-branch=-1
# --max-call-depth=-1
# --max-method-definition=-1
# --exclude=org/mydom/myapp/hoge/*

"""[1:-1].split('\n')

SmallDataLines = """
# --ngram-size=3
# --max-branch=-1
# --max-call-depth=-1
# --max-method-definition=-1

ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
loc:
  ShowWeekdayR.main:([Lj/l/String;)V,15 >1
  ShowWeekdayR.main:([Lj/l/String;)V,38 >0

ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
  java/lang/Integer.parseInt:(Lj/l/String;)I
loc:
  ShowWeekdayR.main:([Lj/l/String;)V,15 >1
  ShowWeekdayR.main:([Lj/l/String;)V,38 >1
  ShowWeekdayR.main:([Lj/l/String;)V,61 >0

"""[1:-1].split('\n')

SmallDataLinenumLines = """
# --ngram-size=3
# --max-branch=-1
# --max-call-depth=-1
# --max-method-definition=-1

ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
loc:
  ShowWeekdayR.java: 14 >1 // main:([Lj/l/String;)V
  ShowWeekdayR.java: 16 >0 // main:([Lj/l/String;)V

ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
  java/lang/Integer.parseInt:(Lj/l/String;)I
loc:
  ShowWeekdayR.java: 14 >1 // main:([Lj/l/String;)V
  ShowWeekdayR.java: 16 >1 // main:([Lj/l/String;)V
  ShowWeekdayR.java: 18 >0 // main:([Lj/l/String;)V

"""[1:-1].split('\n')

DataOfTraceAndMetricLines = """
# --ngram-size=3
# --max-branch=-1
# --max-call-depth=-1
# --max-method-definition=-1

metric-clat= 1
metric-max-depth= 1
ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
trace:
  ShowWeekdayR.main:([Lj/l/String;)V,15 >0
  ShowWeekdayR.main:([Lj/l/String;)V,38 >0
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1
trace:
  ShowWeekdayR.main:([Lj/l/String;)V,38 >0
  ShowWeekdayR.main:([Lj/l/String;)V,61 >0
  ShowWeekdayR.main:([Lj/l/String;)V,72 >0
trace:
  ShowWeekdayR.main:([Lj/l/String;)V,15 >0
  ShowWeekdayR.main:([Lj/l/String;)V,38 >0
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1

metric-clat= 0
metric-max-depth= 1
ope:
  j/l/String.indexOf:(Lj/l/String;)I
  j/l/String.split:(Lj/l/String;)[Lj/l/String;
  java/lang/Integer.parseInt:(Lj/l/String;)I
trace:
  ShowWeekdayR.main:([Lj/l/String;)V,15 >0
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,10 >1
trace:
  ShowWeekdayR.main:([Lj/l/String;)V,38 >0
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1
  ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,10 >1

"""[1:-1].split('\n')


class TestReadCloneIter(unittest.TestCase):
    def testEmptyData(self):
        data = list(cm.read_clone_iter(iter(EmptyDataLines)))
        self.assertTrue(len(data), 1)
        tag, value = data[0]
        self.assertEqual(tag, cm.OPTIONS)
        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        oh.update("ngram-size", 6)
        oh.update("exclude", "org/mydom/myapp/hoge/*")
        self.assertEqual(value, oh)
    
    def testSmallData(self):
        data = list(cm.read_clone_iter(iter(SmallDataLines)))
        self.assertTrue(len(data), 3)

        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        oh.update("ngram-size", 3)
        tag, value = data[0]
        self.assertEqual(tag, cm.OPTIONS)
        self.assertEqual(value, oh)

        tag, value = data[1]
        self.assertEqual(tag, cm.OPESEQ_LOCS)
        self.assertEqual(len(value), 2)
        self.assertSequenceEqual(value[0], ['j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.split:(Lj/l/String;)[Lj/l/String;'])
        self.assertSequenceEqual(value[1], ['ShowWeekdayR.main:([Lj/l/String;)V,15 >1', 'ShowWeekdayR.main:([Lj/l/String;)V,38 >0'])

        tag, value = data[2]
        self.assertEqual(tag, cm.OPESEQ_LOCS)
        self.assertEqual(len(value), 2)
        self.assertSequenceEqual(value[0], ['j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.split:(Lj/l/String;)[Lj/l/String;', 'java/lang/Integer.parseInt:(Lj/l/String;)I'])
        self.assertSequenceEqual(value[1], ['ShowWeekdayR.main:([Lj/l/String;)V,15 >1', 'ShowWeekdayR.main:([Lj/l/String;)V,38 >1', 'ShowWeekdayR.main:([Lj/l/String;)V,61 >0'])

    def testSmallDataLinenum(self):
        data = list(cm.read_clone_iter(iter(SmallDataLinenumLines)))
        self.assertTrue(len(data), 3)

        oh = cm.OptionHolder(cm.CMDLINE_OPTIONS)
        oh.update("ngram-size", 3)
        tag, value = data[0]
        self.assertEqual(tag, cm.OPTIONS)
        self.assertEqual(value, oh)

        tag, value = data[1]
        self.assertEqual(tag, cm.OPESEQ_LOCS)
        self.assertEqual(len(value), 2)
        self.assertSequenceEqual(value[0], ['j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.split:(Lj/l/String;)[Lj/l/String;'])
        self.assertSequenceEqual(value[1], ['ShowWeekdayR.java: 14 >1 // main:([Lj/l/String;)V', 'ShowWeekdayR.java: 16 >0 // main:([Lj/l/String;)V'])

        tag, value = data[2]
        self.assertEqual(tag, cm.OPESEQ_LOCS)
        self.assertEqual(len(value), 2)
        self.assertSequenceEqual(value[0], ['j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.split:(Lj/l/String;)[Lj/l/String;', 'java/lang/Integer.parseInt:(Lj/l/String;)I'])
        self.assertSequenceEqual(value[1], ['ShowWeekdayR.java: 14 >1 // main:([Lj/l/String;)V', 'ShowWeekdayR.java: 16 >1 // main:([Lj/l/String;)V', 'ShowWeekdayR.java: 18 >0 // main:([Lj/l/String;)V'])

    def testDataOfTraceAndMetric(self):
        data = list(cm.read_clone_iter(iter(DataOfTraceAndMetricLines)))
        self.assertTrue(len(data), 5)
        
        tag, value = data[0]
        self.assertEqual(tag, cm.OPTIONS)

        tag, value = data[1]
        self.assertEqual(tag, cm.METRIC_VALUES)
        self.assertSequenceEqual(value, [('metric-clat', 1), ('metric-max-depth', 1)])
        
        tag, value = data[2]
        self.assertEqual(tag, cm.OPESEQ_TRACES)

        ope_list, traces = value
        self.assertSequenceEqual(ope_list, ['j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.indexOf:(Lj/l/String;)I', 'j/l/String.split:(Lj/l/String;)[Lj/l/String;'])
        self.assertEqual(len(traces), 3)
        self.assertSequenceEqual(traces[0], ['ShowWeekdayR.main:([Lj/l/String;)V,15 >0', 'ShowWeekdayR.main:([Lj/l/String;)V,38 >0', 'ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1'])
        self.assertSequenceEqual(traces[1], ['ShowWeekdayR.main:([Lj/l/String;)V,38 >0', 'ShowWeekdayR.main:([Lj/l/String;)V,61 >0', 'ShowWeekdayR.main:([Lj/l/String;)V,72 >0'])
        self.assertSequenceEqual(traces[2], ['ShowWeekdayR.main:([Lj/l/String;)V,15 >0', 'ShowWeekdayR.main:([Lj/l/String;)V,38 >0', 'ShowWeekdayR.setCalendarDate:(Ljava/util/Calendar;Lj/l/String;Lj/l/String;)V,2 >1'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
