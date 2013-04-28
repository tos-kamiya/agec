#coding: utf-8

import unittest

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

import ope_manip as om

body_if_branch = """
       0: iload_1       
       1: ifle          12
       4: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
       7: ldc           #3                  // String x > 0
       9: invokevirtual #4                  // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      12: return        
"""[1:-1].split('\n')

body_for_loop = """
       0: iconst_0      
       1: istore_1      
       2: iload_1       
       3: bipush        10
       5: if_icmpge     34
       8: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      11: ldc           #5                  // String i = %d
      13: iconst_1      
      14: anewarray     #6                  // class java/lang/Object
      17: dup           
      18: iconst_0      
      19: iload_1       
      20: invokestatic  #7                  // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      23: aastore       
      24: invokevirtual #8                  // Method java/io/PrintStream.printf:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/io/PrintStream;
      27: pop           
      28: iinc          1, 1
      31: goto          2
      34: return        
"""[1:-1].split('\n')

body_table_switch = """
       0: iload_1       
       1: tableswitch   { // 1 to 2
                     1: 24
                     2: 35
               default: 46
          }
      24: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      27: ldc           #22                 // String v = 1
      29: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      32: goto          54
      35: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      38: ldc           #30                 // String v = 2
      40: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      43: goto          54
      46: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      49: ldc           #32                 // String others
      51: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      54: return        
"""[1:-1].split('\n')

body_lookup_switch = """
       0: iload_1       
       1: lookupswitch  { // 3
                     1: 36
                    17: 47
                    20: 58
               default: 69
          }
      36: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      39: ldc           #22                 // String v = 1
      41: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      44: goto          77
      47: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      50: ldc           #38                 // String v = 17
      52: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      55: goto          77
      58: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      61: ldc           #40                 // String v = 20
      63: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      66: goto          77
      69: getstatic     #16                 // Field java/lang/System.out:Ljava/io/PrintStream;
      72: ldc           #32                 // String others
      74: invokevirtual #24                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      77: return        
"""[1:-1].split('\n')

class TestOpeManip(unittest.TestCase):
    def testBodyTextToOpeListBranch(self):
        ope_list = om.body_text_to_ope_list(body_if_branch)
        self.assertEqual(len(ope_list), 13)
        self.assertSequenceEqual(ope_list, [
            ('iload_1', (), None), 
            ('ifle', ('12',), None), 
            None, 
            None, 
            ('getstatic', ('#2',), '// Field java/lang/System.out:Ljava/io/PrintStream;'), 
            None, 
            None, 
            ('ldc', ('#3',), '// String x > 0'), 
            None, 
            ('invokevirtual', ('#4',), '// Method java/io/PrintStream.println:(Ljava/lang/String;)V'), 
            None, 
            None, 
            ('return', (), None)
        ])
        om.verify_branch_ope(ope_list)

    def testBodyTextToOpeListLoop(self):
        ope_list = om.body_text_to_ope_list(body_for_loop)
        self.assertEqual(len(ope_list), 35)
        self.assertSequenceEqual(ope_list, [
            ('iconst_0', (), None), 
            ('istore_1', (), None), 
            ('iload_1', (), None), 
            ('bipush', ('10',), None), 
            None, 
            ('if_icmpge', ('34',), None), 
            None, 
            None, 
            ('getstatic', ('#2',), '// Field java/lang/System.out:Ljava/io/PrintStream;'), 
            None, 
            None, 
            ('ldc', ('#5',), '// String i = %d'), 
            None, 
            ('iconst_1', (), None), 
            ('anewarray', ('#6',), '// class java/lang/Object'), 
            None, 
            None, 
            ('dup', (), None), 
            ('iconst_0', (), None), 
            ('iload_1', (), None), 
            ('invokestatic', ('#7',), '// Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;'), 
            None, 
            None, 
            ('aastore', (), None), 
            ('invokevirtual', ('#8',), '// Method java/io/PrintStream.printf:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/io/PrintStream;'), 
            None, 
            None, 
            ('pop', (), None), 
            ('iinc', ('1', '1'), None), 
            None, 
            None, 
            ('goto', ('2',), None), 
            None, 
            None, 
            ('return', (), None)
        ])
        om.verify_branch_ope(ope_list)

    def testBodyTableSwitch(self):
        ope_list = om.body_text_to_ope_list(body_table_switch)
        self.assertEqual(len(ope_list), 55)
        self.assertSequenceEqual(ope_list[:25], [
            ('iload_1', (), None), 
            ('tableswitch', [('1', '24'), ('2', '35'), ('default', '46')], '// 1 to 2'), 
            None, None, None, None, None, None, None, None, None, None, 
            None, None, None, None, None, None, None, None, None, None, 
            None, None, 
            ('getstatic', ('#16',), '// Field java/lang/System.out:Ljava/io/PrintStream;')
        ])
        om.verify_branch_ope(ope_list)

    def testBodyLookupSwitch(self):
        ope_list = om.body_text_to_ope_list(body_lookup_switch)
        self.assertEqual(len(ope_list), 78)
        self.assertSequenceEqual(ope_list[:37], [
            ('iload_1', (), None), 
            ('lookupswitch', [('1', '36'), ('17', '47'), ('20', '58'), ('default', '69')], '// 3'), 
            None, None, None, None, None, None, None, None, None, None, 
            None, None, None, None, None, None, None, None, None, None, 
            None, None, None, None, None, None, None, None, None, None, 
            None, None, None, None, 
            ('getstatic', ('#16',), '// Field java/lang/System.out:Ljava/io/PrintStream;')
        ])
        om.verify_branch_ope(ope_list)
        
    def testVerifyBranchOpe(self):
        ope_list = [
            ('if_icmpge', ('1',), None),
            ('iload_1', (), None),
        ]
        om.verify_branch_ope(ope_list)
        ope_list = ope_list[:1]
        with self.assertRaises(om.InvalidOpe):
            om.verify_branch_ope(ope_list)

        ope_list = [
            ('if_icmpge', ('1',), None),
            None
        ]
        with self.assertRaises(om.InvalidOpe):
            om.verify_branch_ope(ope_list)

    def testFormatOpeList(self):
        ope_list = om.body_text_to_ope_list(body_lookup_switch)
        lines = om.format_ope_list(ope_list)
        original_seq = [re.sub(r'\s+', ' ', L.rstrip()) for L in body_lookup_switch]
        formatted_seq = [re.sub(r'\s+', ' ', L.rstrip()) for L in lines]
        self.assertSequenceEqual(formatted_seq, original_seq)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()