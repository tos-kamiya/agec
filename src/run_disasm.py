#!/usr/bin/env python
#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import os
import sys
import subprocess

def classname_iter(classlist):
    with open(classlist, "rb") as f:
        for L in f:
            classname = L.rstrip().decode("utf-8")
            yield classname

def disassemble(jar, classname):
    text = subprocess.check_output(["/usr/bin/javap", "-c", "-p", "-l", "-constants", "-cp", jar, classname])
    text = text.decode("utf-8")
    return text

def main(argv):
    if len(argv) == 1:
        sys.stdout.write("usage: gen_assemblycode jar classlist -o outputdir\n")
        sys.exit(0)

    jar, classlist, option, outputdir = argv[1:]
    assert option == '-o'

    if not os.path.isdir(outputdir):
        if os.path.exists(outputdir):
            sys.exit("output directory already exists")
        os.mkdir(outputdir)

    for classname in classname_iter(classlist):
        text = disassemble(jar, classname)
        outputfile = os.path.join(outputdir, classname + ".asm")
        with open(outputfile, "wb") as outp:
            outp.write(text.encode("utf-8"))

if __name__ == '__main__':
    main(sys.argv)

