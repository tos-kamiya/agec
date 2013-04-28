#!/usr/bin/env python
#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import re
import os
import sys

import asm_manip as am
import ope_manip as om

UNTRACKED_CLAZS = frozenset(['java/lang/StringBuilder'])

BRANCH_OPES = frozenset([
    "ifeq", "ifnull", "iflt", "ifle", "ifne", "ifnonnull", "ifgt", "ifge",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpgt", "if_icmple", "if_icmpg",
    "if_acmpeq", "if_acmpne",
    ])
RETURN_OPS = ("return", "ireturn", "lreturn", "dreturn", "areturn")
INVOKE_OPS = ("invokevirtual", "invokespecial", "invokestatic", "invokeinterface")

VALID_OPS = set()
VALID_OPS.update(RETURN_OPS)
VALID_OPS.update(["athrow", "goto", "goto_w"])
VALID_OPS.update(BRANCH_OPES)
VALID_OPS.update(["lookupswitch", "tableswitch"])
VALID_OPS.update(INVOKE_OPS)
VALID_OPS = frozenset(VALID_OPS)

def sig_to_claz_method(sig):
    p = sig.find('.')
    assert p >= 0
    claz = sig[:p]
    method = sig[p+1:]
    return claz, method

def sig_to_maybe_claz_method(sig):
    p = sig.find('.')
    if p < 0:
        return None, sig
    claz = sig[:p]
    method = sig[p+1:]
    return claz, method

def claz_method_to_sig(claz, method):
    if claz:
        return "%s.%s" % (claz, method)
    else:
        return method

def make_method2claz2code(sig2code):
    method2claz2code = {}
    for sig, code in sorted(sig2code.iteritems()):
        claz, method = sig_to_claz_method(sig)
        method2claz2code.setdefault(method, {})[claz] = code
    return method2claz2code

_pat_sig = re.compile(r'^//\s+(Interface)?Method\s+(?P<name>.+)$')

def get_claz_method_from_comment(comment, context_claz=None):
    m = _pat_sig.match(comment)
    if m:
        siglike = m.group('name')
        if siglike.find('.') < 0:
            if siglike.startswith('"<init>"'):
                return context_claz, siglike
            else:
                return None, siglike
        else:
            return sig_to_claz_method(siglike)
    return None, None

def gen_code_ngrams(claz, method, method2claz2code, ngram_size, max_call_depth=-1):
    claz2code = method2claz2code.get(method)
    assert claz2code is not None
    ope_list = claz2code.get(claz)
    assert ope_list is not None

    if max_call_depth == -1:
        max_call_depth = ngram_size

    def to_ngram_tuple(q):
        return tuple((invoked_sig, "%s,%d" % (pos_sig, pos_index), depth) for invoked_sig, pos_sig, pos_index, depth in q)

    ngram_set = set()
    cur_gram = []
    cur_call_stack = []

    def collect_ngram(claz, method, ope_list, index, depth, 
            head_index_limit=None):
        #sys.stdout.write("claz,method,index,depth = %s,%s,%d,%d\n" % (claz, method, index, depth))  # for debug
        cur_call_stack_size0 = len(cur_call_stack)
        if (claz, method) == (None, None):
            claz, method = cur_call_stack[-1]
            assert claz is not None
            assert method is not None
        else:
            if (claz, method) in cur_call_stack:  # called recursively?
                return
            cur_call_stack.append((claz, method))

        sig = claz_method_to_sig(claz, method)
        ope_list_len = len(ope_list)

        def find_valid_ope(index):
            while index < ope_list_len:
                ope = ope_list[index]
                if ope is not None and ope[0] in VALID_OPS:
                    return index
                index += 1
            return ope_list_len

        cur_gram_size0 = len(cur_gram)
        try:
            if head_index_limit is None:
                head_index_limit = ope_list_len
            prev_index = index - 1
            while index < ope_list_len:
                assert index > prev_index
                prev_index = index
                ope = ope_list[index]
                if ope is None:
                    index = find_valid_ope(index + 1)
                    continue  # while index
                opecode, operands, comment = ope
                if opecode in RETURN_OPS:
                    return
                elif opecode == "athrow":
                    return
                elif opecode in ("goto", "goto_w"):
                    assert len(operands) == 1
                    dest_index = int(operands[0])
                    if dest_index > index:
                        index = dest_index
                    else:
                        index += 1
                elif opecode in BRANCH_OPES:
                    assert len(operands) == 1
                    dest_index = int(operands[0])
                    if dest_index > index:
                        #sys.stderr.write(">>claz.method=%s.%s<<\n" % (claz, method))
                        collect_ngram(None, None, ope_list, dest_index, depth,
                                head_index_limit)
                        head_index_limit = min(dest_index, head_index_limit)

                    while True:
                        index = find_valid_ope(index + 1)
                        if index >= ope_list_len:
                            break  # while True
                        opecode, operands, comment = ope_list[index]
                        if not (opecode in BRANCH_OPES and int(operands[0]) == dest_index):
                            break  # while True
                elif opecode in ("lookupswitch", "tableswitch"):
                    dest_indices = sorted(set([int(d) for v, d in operands]))
                    for dest_index in dest_indices:
                        if dest_index > index:
                            collect_ngram(None, None, ope_list, dest_index, depth,
                                    head_index_limit)
                    head_index_limit = min(dest_index, head_index_limit)
                    index += 1
                elif opecode in INVOKE_OPS:
                    c, m = get_claz_method_from_comment(comment, context_claz=claz)
                    if c in UNTRACKED_CLAZS:
                        index += 1
                        continue  # while index

                    assert m
                    if depth < max_call_depth and cur_gram:  
                        # a head item of a n-gram should come from the original method.
                        # when the head item is coming from called method, even the original method
                        # belonged to a clone, all of the n-gram items are coming from the called method.
                        c2c = method2claz2code.get(m)
                        if c2c:
                            if c is None:
                                for c, opl in sorted(c2c.iteritems()):
                                    collect_ngram(c, m, opl, 0, depth + 1)
                            else:
                                opl = c2c.get(c)
                                if opl:
                                    collect_ngram(c, m, opl, 0, depth + 1)

                    s = claz_method_to_sig(c, m)
                    #if not cur_gram or cur_gram[-1][0] != s:  # if not a reptitive code
                    #    cur_gram.append((s, sig, index, depth))
                    cur_gram.append((s, sig, index, depth))

                    if len(cur_gram) >= ngram_size:
                        head = cur_gram[-ngram_size]
                        if head[3] != 0:  # escaped from the original method?
                            return
                        if head[1] == sig and head[2] > head_index_limit:
                            # a branch already investegaed opes ahead
                            return
                        ngram_set.add(to_ngram_tuple(cur_gram[-ngram_size:]))

                    index += 1
                else:
                    index += 1
        finally:
            cur_gram[:] = cur_gram[:cur_gram_size0]
            cur_call_stack[:] = cur_call_stack[:cur_call_stack_size0]

    collect_ngram(claz, method, ope_list, 0, 0)

    return list(sorted(ngram_set))

def count_branches(ope_list):
    count = 0
    for index, ope in enumerate(ope_list):
        if ope is None:
            continue  # for index
        opecode, operands, comment = ope
        if opecode in BRANCH_OPES:
            assert len(operands) == 1
            count += 1
        elif opecode in ("lookupswitch", "tableswitch"):
            dest_indices = set([int(d) for v, d in operands])
            count += len(dest_indices)
    return count

def exclude_clazs(method2claz2code, exclude):
    exclude_clazs = frozenset([e for e in exclude if not e.endswith('/*')])
    exclude_packages = frozenset([e[:-1] for e in exclude if e.endswith('/*')])
    
    clazs = set()
    for method, claz2code in method2claz2code.iteritems():
        clazs.update(claz2code.iterkeys())
    clazs_tobe_excluded = set()
    for claz in sorted(clazs):
        if claz in exclude_clazs:
            clazs_tobe_excluded.add(claz)
        else:
            p = claz.rfind('/')
            if p >= 0:
                package = claz[:p + 1]  # include trailing '/'
                if package in exclude_packages:
                    clazs_tobe_excluded.add(claz)
    methods = method2claz2code.keys()
    for method in methods:
        claz2code = method2claz2code[method]
        for c in clazs_tobe_excluded.intersection(claz2code.iterkeys()):
            del claz2code[c]
        if len(claz2code) == 0:
            del method2claz2code[method]
    return clazs_tobe_excluded

def exclude_ctors(method2claz2code):
    ctors = [m for m in method2claz2code.keys() \
            if m.startswith('"<init>"') or m.startswith("access$")]
    for m in ctors:
        del method2claz2code[m]
    return ctors

def remove_empty_method_bodies(method2claz2code):
    def includes_method_invocation(claz, method, ope_list, method2claz2code):
        for ope in ope_list:
            if ope is None:
                continue  # for ope
            if ope[0] in ("invokevirtual", "invokespecial", "invokestatic", "invokeinterface"):
                return True
        return False
    
    empty_claz_methods = []
    for method, claz2code in method2claz2code.iteritems():
        for claz, ope_list in claz2code.iteritems():
            if not includes_method_invocation(claz, method, ope_list, method2claz2code):
                empty_claz_methods.append((claz, method))

    for c, m in empty_claz_methods:
        del method2claz2code[m][c]
        if len(method2claz2code[m]) == 0:
            del method2claz2code[m]

    return empty_claz_methods

def remove_too_many_branch_method_bodies(method2claz2code, max_branch):
    if max_branch < 0:
        return []

    too_many_branch_methods = []
    for method, claz2code in method2claz2code.iteritems():
        for claz, ope_list in claz2code.iteritems():
            branch_count = count_branches(ope_list)
            if branch_count > max_branch:
                too_many_branch_methods.append((claz, method))

    for c, m in too_many_branch_methods:
        del method2claz2code[m][c]
        if len(method2claz2code[m]) == 0:
            del method2claz2code[m]

    return too_many_branch_methods

def remove_too_many_definition_methods(method2claz2code, max_method_definition):
    assert max_method_definition > 0
    too_many_definition_methods = [method \
            for method, claz2code in method2claz2code.iteritems() \
            if len(claz2code) > max_method_definition]
    for m in too_many_definition_methods:
        del method2claz2code[m]
    return too_many_definition_methods

def main(argv):
    from argparse import ArgumentParser
    psr = ArgumentParser(description='Generate n-grams of method calls')
    psr.add_argument('asmdir', nargs=1)

    psr.add_argument('-n', '--ngram-size', action='store', type=int, default=6)
    psr.add_argument('-v', '--verbose', action='store_true')
    psr.add_argument('--max-branch', action='store', type=int, default=-1,
            help='max branches in a method (such as ifs and switch-cases). =-1 means unlimited')
    psr.add_argument('--max-call-depth', action='store', type=int, default=-1,
            help='max depth in expanding method calls. =-1 means specify ngram-size as limit')
    psr.add_argument('--max-method-definition', action='store', type=int, default=-1,
            help='max method defintions for a signiture. =-1 means unlimited')
    psr.add_argument('--target-class-method', action='store', nargs='*')
    psr.add_argument('-e', '--exclude', action='store', nargs='*',
            help="specify classes by fully-qualified name, e.g. org/myapp/MyClass$AInnerClass. A wildcard '*' can be used as class name, e.g. org/myapp/*")
    psr.add_argument('--include-ctors', action='store_true',
            help='include "<init>" and access$... methods as targets')

    psr.add_argument('--mode-diagnostic', action='store_true',
            help='show bytecode info and the filtering results')
    psr.add_argument('--mode-method-signature', action='store_true',
            help='show method signatures')
    psr.add_argument('--mode-method-body', action='store_true',
            help='show method bodies (byte code)')

    psr.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = psr.parse_args(argv[1:])

    if sum(filter(None, [args.mode_method_signature, args.mode_method_body, 
            args.mode_diagnostic])) >= 2:
        sys.exit("--mode-* options are mutually exclusive")
    asmdir = args.asmdir[0]
    mode_method_signature = args.mode_method_signature
    mode_method_body = args.mode_method_body
    verbose = args.verbose
    ngram_size = args.ngram_size
    max_call_depth = max(-1, args.max_call_depth)
    max_branch = max(-1, args.max_branch)
    max_method_definition = max(-1, args.max_method_definition)
    exclude = set(args.exclude if args.exclude else [])
    target_class_methods = frozenset(args.target_class_method) if args.target_class_method else None
    include_ctors = args.include_ctors
    mode_diagnostic = args.mode_diagnostic

    if not os.path.isdir(asmdir):
        sys.exit("error: fail to access asmdir: %s" % asmdir)

    sig2code = {}
    #sig2exceptiontable = {}
    #sig2linenumbertable = {}

    for asm_file, sig, code, etbl, ltbl in am.get_method_code_and_tables_iter(asmdir):
        sig2code[sig] = tuple(code)
        #sig2exceptiontable[sig] = etbl
        #sig2linenumbertable[sig] = ltbl

    if mode_method_signature:
        for sig in sorted(sig2code.keys()):
            sys.stdout.write(('%s\n' % sig).encode('utf-8'))
    elif mode_method_body:
        for sig, method_body in sorted(sig2code.iteritems()):
            ol = om.body_text_to_ope_list(method_body, sig)
            try:
                om.verify_branch_ope(ol)
            except om.InvalidOpe as e:
                raise om.InvalidOpe("%s: %s" % (sig, str(e)))
            t = ('u%s\n' % sig).encode('utf-8')
            sys.stdout.write(t)
            for L in om.format_ope_list(ol): #, fields=om.FORMAT_FIELD.OPE):
                t = (u'%s\n' % L).encode('utf-8')
                sys.stdout.write(t)
    elif mode_diagnostic:
        sig2oplist = {}
        for sig, method_body in sorted(sig2code.iteritems()):
            ol = om.body_text_to_ope_list(method_body, sig)
            sig2oplist[sig] = ol
        del sig2code

        method2claz2code = make_method2claz2code(sig2oplist)
        del sig2oplist

        if not include_ctors:
            ctors = exclude_ctors(method2claz2code)
            sys.stdout.write("removed ctors: %d\n" % len(ctors))

        if exclude:
            claz_excluded = exclude_clazs(method2claz2code, exclude)
            sys.stdout.write("removed classes by option --exclude: %d\n" % \
                    len(claz_excluded))

        claz_set = set()
        method_defs = 0
        for m, c2c in method2claz2code.iteritems():
            claz_set.update(c2c.iterkeys())
            method_defs += len(c2c)
        sys.stdout.write("classes: %d\n" % len(claz_set))
        sys.stdout.write("method bodies: %d\n" % method_defs)
        del claz_set

        empty_claz_methods = remove_empty_method_bodies(method2claz2code)
        sys.stdout.write("empty method bodies: %d\n" % len(empty_claz_methods))

        if max_branch >= 0:
            too_many_branch_methods = \
                    remove_too_many_branch_method_bodies(method2claz2code, max_branch)
            sys.stdout.write("removed method bodies by option --max-branch=%d: %d\n" % \
                    (max_branch, len(too_many_branch_methods)))

        if max_method_definition > 0:
            too_many_definition_methods = remove_too_many_definition_methods(
                    method2claz2code, max_method_definition)
            sys.stdout.write("removed methods by option --max-definition=%d: %d\n" % \
                    (max_method_definition, len(too_many_definition_methods)))
    else:
        sig2oplist = {}
        for sig, method_body in sorted(sig2code.iteritems()):
            ol = om.body_text_to_ope_list(method_body, sig)
            sig2oplist[sig] = ol
        del sig2code

        method2claz2code = make_method2claz2code(sig2oplist)
        del sig2oplist

        if not include_ctors:
            ctors = exclude_ctors(method2claz2code)
            verbose and sys.stderr.write("> removed %d ctors\n" % len(ctors))

        if exclude:
            claz_excluded = exclude_clazs(method2claz2code, exclude)
            verbose and sys.stderr.write("> removed %d classes by option --exclude\n" % \
                    len(claz_excluded))

        empty_claz_methods = remove_empty_method_bodies(method2claz2code)
        verbose and sys.stderr.write("> found %d empty method bodies\n" % len(empty_claz_methods))

        if max_branch >= 0:
            too_many_branch_methods = remove_too_many_branch_method_bodies(max_branch)
            verbose and sys.stderr.write("> removed %d method bodies by option --max-branch=%d\n" % \
                    (len(too_many_branch_methods), max_branch))

        if max_method_definition > 0:
            too_many_definition_methods = remove_too_many_definition_methods(max_method_definition)
            verbose and sys.stderr.write("> removed %d methods by option --max-definition=%d\n" % \
                    (len(too_many_definition_methods), max_method_definition))

        sys.stdout.write("# --ngram-size=%d\n" % ngram_size)
        sys.stdout.write("# --max-branch=%d\n" % max_branch)
        sys.stdout.write("# --max-call-depth=%d\n" % max_call_depth)
        sys.stdout.write("# --max-method-definition=%d\n" % max_method_definition)
        if include_ctors:
            sys.stdout.write("# --include-ctors\n")
        for e in exclude:
            sys.stdout.write("# --exclude=%s\n" % e)
        sys.stdout.write('\n')
        for method, claz2code in sorted(method2claz2code.iteritems()):
            for claz, code in sorted(claz2code.iteritems()):
                if target_class_methods and ("%s.%s" % (claz, method)) not in target_class_methods:
                    continue  # for claz
                verbose and sys.stderr.write('> %s.%s\n' % (claz, method))
                code_ngrams = gen_code_ngrams(claz, method, method2claz2code,
                        ngram_size, max_call_depth=max_call_depth) 
                for ngram in code_ngrams:
                    s = ''.join("%s\t%s\t%d\n" % (op, loc, depth) for op, loc, depth in ngram)
                    sys.stdout.write((s + '\n').encode('utf-8'))

if __name__ == '__main__':
    main(sys.argv)

