#!/usr/bin/env python
#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

"""
A helper script to convert each file path (of .class file) into class name
The only supposed usage is:
  java JarFileList some_jar_file.jar | python filepath2class.py > classlist.txt
"""

import sys

def main(argv):
    for L in sys.stdin:
        L = L.rstrip()
        if L.endswith(".class"):
            L = L[:-len(".class")]
            sys.stdout.write("%s\n" % L.replace("/", "."))

if __name__ == '__main__':
    main(sys.argv)
