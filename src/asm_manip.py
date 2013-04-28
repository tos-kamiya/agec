#coding: utf-8

"""
javap's disassembled file manipulation.
"""

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import os
import re

import type_formatter as tf

def indent_width(L):
    for i, c in enumerate(L):
        if c != ' ':
            return i
    return 0

def asm_file_iter(asmdir):
    for root, dirs, files in os.walk(asmdir):
        for f in files:
            if f.endswith(".asm"):
                yield os.path.join(root, f)

def asm_filetext_iter(asmdir):
    for asmfile in asm_file_iter(asmdir):
        with open(asmfile, "rb") as f:
            lines = f.read().decode('utf-8').split('\n')
            yield asmfile, lines

def remove_generics_args(s):
    s0 = s
    c = ''
    p = s.find('//')
    if p >= 0:
        s, c = s[:p], s[p:]

    p = s.rfind('<')
    while p >= 0:
        q = s.index('>', p)
        assert q >= 0
        s = s[:p] + s[q+1:]
        p = s.rfind('<')

    return s + c

def split_into_method_iter(asmfile, lines):
    typ = r'(\w|[.$\[\]])+'
    pat_class = re.compile(r'^((public|private|final|abstract|strictfp) +)*class +(?P<id>TYP) +({|extends|implements)'.replace('TYP', typ))
    pat_interface = re.compile(r'^((public|private|abstract|strictfp) +)*interface +(?P<id>TYP) +({|extends)'.replace('TYP', typ))
    pat_static = re.compile(r'^  static +{};$')
    pat_method = re.compile(r'^  ((public|private|protected|final|abstract|synchronized|static) +)*(?P<retv>TYP) +(?P<name>[\w$]+)[(](?P<args>((TYP, )*TYP)?)[)](;| +throws)'.replace('TYP', typ))
    pat_ctor = re.compile(r'^  ((public|private|protected) +)*(?P<name>TYP)[(](?P<args>((TYP, )*TYP)?)[)](;| +throws)'.replace('TYP', typ))

    def pack(class_name, method_sig, method_body, asmfile):
        if class_name == None:
            assert False
        p = class_name.find('<')
        if p >= 0:
            class_name = class_name[:p]
        return (class_name, method_sig, method_body, asmfile)

    class_name, method_sig, method_body = None, None, None

    for ln, L in enumerate(lines):
        if not L: continue # skip empty lines
        L = remove_generics_args(L)

        iw = indent_width(L)
        if iw == 0:
            m = pat_class.match(L)
            if m:
                if class_name and method_sig:
                    yield pack(class_name, method_sig, method_body, asmfile)
                    class_name, method_sig, method_body = None, None, None
                class_name = m.group('id')
            else:
                m = pat_interface.match(L)
                if m:
                    if class_name and method_sig:
                        yield pack(class_name, method_sig, method_body, asmfile)
                        class_name, method_sig, method_body = None, None, None
                    class_name = None
                else:
                    if L.startswith("Compiled from ") or L == "}":
                        pass
                    else:
                        raise AssertionError("unexpected line: %s: %d: %s" % (asmfile, ln + 1, L))
        elif iw == 2:
            m = pat_method.match(L)
            if m:
                if class_name and method_sig:
                    yield pack(class_name, method_sig, method_body, asmfile)
                    method_sig, method_body = None, None
                args = m.group('args') or ''
                method_sig = (m.group('name'),
                        tuple(filter(None, args.split(', '))),
                        m.group('retv'))
                method_body = []
            else:
                m = pat_ctor.match(L)
                if m:
                    if class_name and method_sig:
                        yield pack(class_name, method_sig, method_body, asmfile)
                        method_sig, method_body = None, None
                    args = m.group('args') or ''
                    method_sig = ('"<init>"',
                            tuple(filter(None, args.split(', '))),
                            'void')
                    method_body = []
                else:
                    m = pat_static.match(L)
                    if m:
                        if class_name and method_sig:
                            yield pack(class_name, method_sig, method_body, asmfile)
                            method_sig, method_body = None, None
                        method_sig = ('"static{}"', (), 'void')
                        method_body = []
        else:
            method_body.append(L)

    if class_name and method_sig:
        yield pack(class_name, method_sig, method_body, asmfile)
        class_name, method_sig, method_body = None, None, None

def split_method_body_to_code_and_tables(method_body_lines):
    code_lines = []
    exceptiontable_lines = []
    linenumbertable_lines = []
    target = dummy = []
    for L in method_body_lines:
        if L == "    Code:":
            target = code_lines
        elif L == "    Exception table:":
            target = exceptiontable_lines
        elif L == "    LineNumberTable:":
            target = linenumbertable_lines
        elif L == "    LocalVariableTable:":
            target = dummy
        else:
            target.append(L)
    return code_lines, exceptiontable_lines, linenumbertable_lines

def get_method_code_and_tables_iter(asm_dir):
    """
    Iterate each method definition of each disassembled file in 'asm_dir' directory.
    Yielded values
       asm_file: file name of the disassmbled file (str)
       sig: signature of the method (str)
       code: definition of the method (list of str)
       exception table: exception table of the method (list of str)
       linenum_table: line number table (list of str)
    """

    def split_into_method_iter_from_asmdir(asmdir):
        for asmfile, lines in asm_filetext_iter(asmdir):
            for v in split_into_method_iter(asmfile, lines):
                yield v

    for claz, method_sig, body, asm_file in split_into_method_iter_from_asmdir(asm_dir):
        name, args, retv = method_sig
        sig = tf.format_sig_in_javap_comment_style(claz, name, args, retv)
        code, exception_table, linenum_table = split_method_body_to_code_and_tables(body)
        yield asm_file, sig, code, exception_table, linenum_table
