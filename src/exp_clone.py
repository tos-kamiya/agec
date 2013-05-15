#!/usr/bin/env python
#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import re
import sys

import asm_manip as am
import ope_manip as om
import type_formatter as tf
import clonefile_manip as cm

import gen_ngram as ng

def extract_class_from_loc_linenum(L):
    pat_loc_linenum = re.compile(r'^\s*([\w_$/.]+)[.]java\s*:\s*(\d+)\s+>\s*(\d+)\s*//\s*(.+)$')
    m = pat_loc_linenum.match(L)
    if m is None:
        return None

    claz_like, method_like = m.group(1), m.group(4)

    p = method_like.find("(")
    assert p >= 0
    q = method_like[:p].find('.')
    if q >= 0:
        inner_claz = method_like[:q]
        method_like = method_like[q+1:]
        claz_like += "$" + inner_claz

    claz, sig = tf.scan_in_javap_comment_style(claz_like + "." + method_like)
    return claz, sig

class ParseError(ValueError):
    pass

def extract_poeseq_and_ngrams(opeseq, locs, method2claz2code, ngram_size, max_call_depth=-1):
    if opeseq == 0:
        raise ParseError("empty ope sequence")
    if ngram_size == -1:
        ngram_size = len(opeseq)
    else:
        if len(opeseq) != ngram_size:
            raise ParseError("length of ope sequence doesn't match to --ngram-size agrgument")
        ngram_size = len(opeseq)

    pat_loc_index = re.compile(r'\s*([^,]+),\s*(\d+)\s*>(\d+)')

    target_claz_methods = None
    if locs is not None:
        tcm_set = set()
        target_claz_methods = []
        for L in locs:
            cs = extract_class_from_loc_linenum(L)
            if cs:
                claz, sig = cs
            else:
                m = pat_loc_index.match(L)
                if m:
                    claz_sig = m.group(1)
                    claz, sig = tf.scan_in_javap_comment_style(claz_sig)
                else:
                    raise ParseError("invalid loc line: %s" % L)
            cm = (claz, sig)
            if cm not in tcm_set:
                tcm_set.add(cm)
                target_claz_methods.append(cm)
        del tcm_set

    target_opeseq = opeseq

    traces = []
    if target_claz_methods is None:
        for method, claz2code in sorted(method2claz2code.iteritems()):
            for claz, code in sorted(claz2code.iteritems()):
                code_ngrams = ng.gen_code_ngrams(claz, method, method2claz2code,
                        ngram_size, max_call_depth=max_call_depth)
                for ngram in code_ngrams:
                    opeseq = [ope for ope, _, _ in ngram]
                    if opeseq == target_opeseq:
                        traces.append(ngram)
    else:
        for claz, method in target_claz_methods:
            c2c = method2claz2code.get(method)
            assert c2c != None
            code = c2c.get(claz)
            assert code != None
            code_ngrams = ng.gen_code_ngrams(claz, method, method2claz2code,
                    ngram_size, max_call_depth=max_call_depth)
            for ngram in code_ngrams:
                opeseq = [ope for ope, _, _ in ngram]
                if opeseq == target_opeseq:
                    traces.append(ngram)

    nonduplicated_traces = [trace for trace, next_trace in \
            zip(traces, traces[1:] + [None]) if trace != next_trace]
    return nonduplicated_traces

def extract_clat(ngrams):
    # common location among traces
    if not ngrams:
        return []

    common_locs = set([loc for _, loc, _ in ngrams[0]])
    for ngram in ngrams[1:]:
        locs = set([loc for _, loc, _ in ngram])
        common_locs.intersection_update(locs)

    return common_locs

def extract_max_depth(ngrams):
    if not ngrams:
        return 0

    max_depth = max(depth for ngram in ngrams for _, _, depth in ngram)
    return max_depth

def main(argv):
    from argparse import ArgumentParser
    psr = ArgumentParser(description="Expand clone's each location to a trace")
    psr.add_argument('asmdir', nargs=1)
    psr.add_argument('clonefile', nargs=1,
            help='part of clone file, which includes options and a clone to be expanded. specify @ to read from stdin')
    psr.add_argument('-t', '--loc-to-trace', action='store_true',
            help='expand each clone location to trace')
    psr.add_argument('-c', '--add-metric-clat', action='store_true',
            help='add common-location-among-traces metric to each clone')
    psr.add_argument('-d', '--add-metric-max-depth', action='store_true',
            help='add max-depth metric to each clone')
    psr.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = psr.parse_args(argv[1:])

    asmdir = args.asmdir[0]
    clonefile = args.clonefile[0]
    add_metric_clat = args.add_metric_clat
    add_metric_max_depth = args.add_metric_max_depth
    loc_to_trace = args.loc_to_trace

    if not (add_metric_clat or loc_to_trace):
        sys.exit("no action specfield. specify -t, -c, -d or mix of them")

    def itfunc():
        for sec, data in cm.read_clone_file_iter(clonefile):
            yield sec, data
    clonefile_iter = itfunc()

    for sec, data in clonefile_iter:
        if sec == cm.OPTIONS:
            clone_data_args = data
            break  # for sec
        else:
            sys.exit('clonefile missing option section')

    ngram_size = clone_data_args.ngram_size
    max_branch = clone_data_args.max_branch
    max_call_depth = clone_data_args.max_call_depth
    max_method_definition = clone_data_args.max_method_definition
    exclude = clone_data_args.exclude

    sig2code = {}
    #sig2exceptiontable = {}
    sig2linenumbertable = {}

    for asm_file, sig, code, etbl, ltbl in am.get_method_code_and_tables_iter(asmdir):
        sig2code[sig] = tuple(code)
        #sig2exceptiontable[sig] = etbl
        sig2linenumbertable[sig] = ltbl

    sig2oplist = {}
    for sig, method_body in sorted(sig2code.iteritems()):
        ol = om.body_text_to_ope_list(method_body, sig)
        sig2oplist[sig] = ol
    del sig2code

    method2claz2code = ng.make_method2claz2code(sig2oplist)
    del sig2oplist

    if exclude:
        ng.exclude_clazs(method2claz2code, exclude)

    ng.remove_empty_method_bodies(method2claz2code)

    if max_branch >= 0:
        ng.remove_too_many_branch_method_bodies(method2claz2code, max_branch)

    if max_method_definition > 0:
        ng.remove_too_many_definition_methods(method2claz2code, max_method_definition)

    if ngram_size < 0:
        clone_data_args.delete("ngram-size")
    for L in clone_data_args.format():
        sys.stdout.write("%s\n" % L)
    sys.stdout.write('\n')  # separator

    try:
        for sec, data in clonefile_iter:
            if sec == cm.OPESEQ_LOCS:
                opeseq, locs = data
            elif sec == cm.OPESEQ_TRACES:
                opeseq, traces = data
                locs = [l[0] for l in traces]
            elif sec == cm.OPESEQ_SINGLE:
                opeseq, _ = data
                locs = None
            else:
                continue  # for sec

            ngrams = extract_poeseq_and_ngrams(opeseq, locs, method2claz2code, 
                    ngram_size, max_call_depth=max_call_depth)

            if add_metric_clat:
                clat = extract_clat(ngrams)
                sys.stdout.write(('metric-clat= %d\n' % len(clat)).encode('utf-8'))

            if add_metric_max_depth:
                max_depth = extract_max_depth(ngrams)
                sys.stdout.write(('metric-max-depth= %d\n' % max_depth).encode('utf-8'))

            sys.stdout.write('ope:\n')
            for L in opeseq:
                sys.stdout.write(('  %s\n' % L).encode('utf-8'))

            if loc_to_trace:
                for ngram in ngrams:
                    sys.stdout.write('trace:\n')
                    for _, loc, depth in ngram:
                        sys.stdout.write(('  %s >%d\n' % (loc, depth)).encode('utf-8'))
            else:
                sys.stdout.write('loc:\n')
                for loc in locs:
                    sys.stdout.write(('  %s\n' % loc).encode('utf-8'))
            sys.stdout.write('\n')
    except cm.CloneFileSyntaxError as e:
        sys.exit(unicode(e).encode('utf-8'))
    except ParseError as e:
        sys.exit(unicode(e).encode('utf-8'))

if __name__ == '__main__':
    main(sys.argv)

