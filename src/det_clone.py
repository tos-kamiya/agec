#!/usr/bin/env python
#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import sys

from enum_generator import EnumGenerator

def readline_iter(filename):
    if filename != '-':
        with open(filename, "rb") as f:
            for L in f:
                L = L.decode('utf-8').rstrip()
                yield L
    else:
        for L in sys.stdin:
            L = L.decode('utf-8').rstrip()
            yield L

def read_ngram_iter(ngram_file):
    cur_opes, cur_locs, cur_deps = [], [], []
    for L in readline_iter(ngram_file):
        if L.startswith('#'):
            yield None, L, None
        elif L == '':  # separator of ngram
            if cur_opes:
                oseq = tuple(cur_opes)
                ls = tuple(cur_locs)
                ds = tuple(cur_deps)
                yield oseq, ls, ds
                cur_opes, cur_locs, cur_deps = [], [], []
        else:
            ope, loc, dep = L.split('\t')
            cur_opes.append(ope)
            cur_locs.append(loc)
            cur_deps.append(int(dep))

def gen_argpsr():
    from argparse import ArgumentParser
    from _version_data import VERSION
    psr = ArgumentParser(description='Generate n-grams of method calls')
    psr.add_argument('ngramfile', nargs=1,
            help='input n-gram file. specify @ to read from stdin')
    psr.add_argument('-x', '--all-ope-seq-per-loc-set', action='store_true',
            help='show all ope sequences for a clone (a set of locations)')
    psr.add_argument('--diagnostic', action='store_true') 
    psr.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    return psr

def main(argv):
    psr = gen_argpsr()
    args = psr.parse_args(argv[1:])

    ngram_file = args.ngramfile[0]
    all_ope_seq = args.all_ope_seq_per_loc_set
    diagnostic = args.diagnostic

    ope2locs = {}
    ope_enum = EnumGenerator()
    loc_enum = EnumGenerator()
    oiseq_startingli2dep = {}

    comment_lines = []

    ngram_count = 0
    for oseq, lseq, dseq in read_ngram_iter(ngram_file):
        ngram_count += 1
        if oseq is None:
            comment_lines.append(lseq)
        else:
            oiseq = tuple(map(ope_enum.to_int, oseq))
            liseq = tuple(map(loc_enum.to_int, lseq))
            ope2locs.setdefault(oiseq, []).append(liseq)
            startingli = liseq[0]
            oiseq_startingli = (oiseq, startingli)
            d = oiseq_startingli2dep.get(oiseq_startingli, sys.maxint)
            oiseq_startingli2dep[oiseq_startingli] = min(d, dseq[-1])

    for L in comment_lines:
        sys.stdout.write('%s\n' % L.encode('utf-8'))
        if all_ope_seq:
            sys.stdout.write('# --all-ope-seq-per-loc-set\n')
    sys.stdout.write('\n')

    distinct_ope_count = len(ope2locs)
    soleloc_ope_count = 0
    clone_ope_count = 0
    done_startinglis_set = set()
    for oiseq, liseqs in sorted(ope2locs.iteritems()):
        if len(liseqs) < 2:  # single appearance?
            soleloc_ope_count += 1
            continue  
        startinglis = sorted(set(liseq[0] for liseq in liseqs))
        if len(startinglis) < 2:  # ope seqs are sharing a starting location?
            soleloc_ope_count += 1
            continue

        if not all_ope_seq:
            t = tuple(startinglis)
            if t in done_startinglis_set:
                soleloc_ope_count += 1
                continue
            done_startinglis_set.add(t)

        clone_ope_count += 1

        sys.stdout.write('ope:\n')
        for opei in oiseq:
            ope = ope_enum.to_str(opei)
            sys.stdout.write('  %s\n' % ope)

        sys.stdout.write('loc:\n')
        for loci in startinglis:
            depth = oiseq_startingli2dep.get((oiseq, loci))
            assert depth is not None
            loc = loc_enum.to_str(loci)
            sys.stdout.write('  %s >%d\n' % (loc, depth))
        sys.stdout.write('\n')

    if diagnostic:
        sys.stdout.write("# locs of valid ngrams: %d\n" % ngram_count)
        sys.stdout.write("# distinct ope seqs: %d\n" % distinct_ope_count)
        sys.stdout.write("#   sole-location ope seqs: %d\n" % soleloc_ope_count)
        sys.stdout.write("#   clone ope seqs: %d\n" % clone_ope_count)

if __name__ == '__main__':
    main(sys.argv)

